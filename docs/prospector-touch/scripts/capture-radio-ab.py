#!/usr/bin/env python3
"""Capture both explicit ports once, guide ABBA, summarize Dongle cadence, bundle evidence."""
import argparse,datetime,json,os,re,selectors,signal,subprocess,sys,time,zipfile
from pathlib import Path
ANSI=re.compile(r'\x1b\[[0-9;]*m')
STAMP=re.compile(r'\[(\d+):(\d+):(\d+)\.(\d+),(\d+)\]')
BINS=['lt1','b1_6','b6_10','b10_14','b14_20','b20_30','b30_50','ge50']

def fields(line):return {k:int(v) for k,v in re.findall(r'\b(\w+)=(-?\d+)(?=\s|$)',line)}

def summarize(text, run):
    phases={};ended=False;aborted=False;rows=[];last={};seen=set();restored=False
    for line in ANSI.sub('',text).splitlines():
        v=fields(line)
        if 'SCANAB ' in line and v.get('run')==run:
            event=re.search(r'event=(\w+)',line)
            if event and event[1]=='PHASE':phases[v['phase']]=v
            if event and event[1]=='END':
                ended=True;restored=v.get('err')==0 and v.get('scan')==1 and v.get('links')==1
            if event and event[1] in ['ABORT','REJECT']:aborted=True
        if 'CAD stage=' not in line:continue
        stage=re.search(r'CAD stage=(RX|USB)\b',line);m=STAMP.search(line)
        if not(stage and m and set(BINS+['frames']).issubset(v)):continue
        ts=int(m[1])*3600+int(m[2])*60+int(m[3])+int(m[4])/1000+int(m[5])/1e6
        key=(stage[1],ts)
        if key in seen:continue
        seen.add(key);prev=last.get(stage[1]);last[stage[1]]=ts
        if prev is not None and 0<ts-prev<4:rows.append((stage[1],prev,ts,v))
    valid=(ended and restored and not aborted and set(phases)=={1,2,3,4} and
           all(p.get('err')==0 and p.get('links')==1 and p.get('scan')==(1 if n in [1,4] else 0)
               for n,p in phases.items()))
    stats={}
    for mode in ['ON','OFF']:
        stats[mode]={}
        for stage in ['RX','USB']:
            selected=[]
            for n,p in phases.items():
                if (n in [1,4])!=(mode=='ON'):continue
                start=p['t_ms']/1000
                end=phases[n+1]['t_ms']/1000 if n<4 and n+1 in phases else start+20
                selected.extend(v for s,a,b,v in rows if s==stage and a>=start+2 and b<=end-1)
            total={k:sum(v[k] for v in selected) for k in BINS};count=sum(total.values())
            stats[mode][stage]=dict(windows=len(selected),frames=sum(v['frames'] for v in selected),intervals=count,bins=total,
                pct6_10=100*total['b6_10']/count if count else None,
                pct30_50=100*total['b30_50']/count if count else None)
    return dict(valid_scan_sequence=valid,phases=phases,statistics=stats,
                limits='Complete Dongle windows only, exclude 2s after/1s before transitions. Includes real pauses. HCI event counts are not mouse frames; host receive timestamps are approximate, not synchronized device clocks.')


def summarize_hci(events, run):
    """Conservative host-receive alignment; retain raw device clocks as evidence."""
    phases={};end=None;records=[];previous=None
    for row in events:
        line=row['line'];v=fields(line);t=row['host_elapsed_s']
        if row['role']=='dongle' and 'SCANAB ' in line and v.get('run')==run:
            if 'event=PHASE ' in line:phases[v['phase']]=t
            elif 'event=END ' in line:end=t
        if row['role']=='right' and 'HCI version=8 ' in line:
            if previous is not None and 1<t-previous<4 and set(BINS+['matched','avg_us','max_us','orphan','overflow','reset','err']).issubset(v):
                if sum(v[k] for k in BINS)==v['matched']:records.append((previous,t,v))
            previous=t
    result={}
    for mode in ['ON','OFF']:
        selected=[]
        for n,start in phases.items():
            stop=phases.get(n+1,end)
            if stop is None or (n in [1,4])!=(mode=='ON'):continue
            selected.extend(v for a,b,v in records if a>=start+3 and b<=stop-2)
        count=sum(v['matched'] for v in selected)
        result[mode]=dict(windows=len(selected),matched=count,
            weighted_avg_us=sum(v['matched']*v['avg_us'] for v in selected)/count if count else None,
            max_us=max((v['max_us'] for v in selected),default=0),
            bins={k:sum(v[k] for v in selected) for k in BINS},
            anomalies={k:sum(v[k] for v in selected) for k in ['orphan','overflow','reset','err']})
    return result

def run_capture(dongle,right,folder):
    folder.mkdir(parents=True,exist_ok=False)
    token=time.time_ns()%1000000000 or 1
    capture=Path(__file__).with_name('capture-right-profile.py')
    selector=selectors.DefaultSelector();children={};buffers={};hci_seen=False;phases={};ended=False;failed=None
    started=time.monotonic();slow_due=None
    journal=(folder/'host-events.jsonl').open('x')
    try:
        for role,port in [('right',right),('dongle',dongle)]:
            command=[sys.executable,str(capture),'--port',port,'--output',str(folder/(role+'.log')),'--seconds','95']
            if role=='dongle':command+=['--scan-ab-run',str(token)]
            child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            children[role]=child;buffers[role]='';selector.register(child.stdout,selectors.EVENT_READ,role)
        print('开始双端采集；约 95 秒自动结束。先静止，等待第 1 段提示。',flush=True)
        while selector.get_map():
            elapsed=time.monotonic()-started
            if elapsed>105:raise RuntimeError('采集超时')
            if elapsed>12 and (not hci_seen or 1 not in phases):
                raise RuntimeError('未收到新版右侧 HCI 或 Dongle 开始确认；请核对两个端口及 T5-08 固件')
            if slow_due and time.monotonic()>=slow_due:
                print('现在改为慢速精细移动，保持到下一段提示。',flush=True);slow_due=None
            for key,_ in selector.select(.2):
                role=key.data;chunk=os.read(key.fileobj.fileno(),8192)
                if not chunk:
                    selector.unregister(key.fileobj);continue
                buffers[role]+=chunk.decode(errors='replace')
                while '\n' in buffers[role]:
                    line,buffers[role]=buffers[role].split('\n',1);line=ANSI.sub('',line).strip();v=fields(line)
                    if any(t in line for t in ['CAD stage=','HCI version=','BTSTAT ','SCANAB ','PIPE ']):
                        journal.write(json.dumps(dict(role=role,host_elapsed_s=time.monotonic()-started,line=line),ensure_ascii=False)+'\n');journal.flush()
                    if role=='right' and 'HCI version=8 ' in line:hci_seen=True
                    if role=='dongle' and 'SCANAB ' in line and v.get('run')==token:
                        event=re.search(r'event=(\w+)',line)
                        if event and event[1]=='PHASE':
                            n=v.get('phase');phases[n]=v
                            if v.get('err') or v.get('links')!=1 or v.get('scan')!=(1 if n in [1,4] else 0):
                                raise RuntimeError('扫描切换失败或连接数量不是 1，停止对照')
                            print(f"第 {n}/4 段：扫描 {'开' if v['scan'] else '关'}。先中速匀速滚球 10 秒。",flush=True)
                            slow_due=time.monotonic()+10
                        elif event and event[1] in ['ABORT','REJECT']:
                            raise RuntimeError('设备拒绝或中止扫描对照；日志已保留')
                        elif event and event[1]=='END':
                            if v.get('err') or v.get('scan')!=1 or v.get('links')!=1:
                                raise RuntimeError('未确认恢复正常扫描；请保留日志并重启 Dongle')
                            ended=True;slow_due=None
                            print('80 秒对照完成，已请求恢复正常扫描。请停手，等待日志保存。',flush=True)
        for child in children.values():
            if child.wait(timeout=3):raise RuntimeError('串口采集器退出失败，请查看日志或端口占用')
        if not ended or not hci_seen:raise RuntimeError('缺少固件 END 或右侧 HCI 确认，不作扫描效果判断')
    except (Exception,KeyboardInterrupt) as error:
        failed=str(error) or '用户中止'
        print('采集中止：'+failed,file=sys.stderr)
    finally:
        for child in children.values():
            if child.poll() is None:child.send_signal(signal.SIGINT)
        for child in children.values():
            try:child.wait(timeout=4)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        journal.close();selector.close()
        result=summarize((folder/'dongle.log').read_text(errors='replace'),token) if (folder/'dongle.log').exists() else {}
        result.update(run=token,dongle_port=dongle,right_port=right,error=failed,hci_seen=hci_seen,elapsed_s=time.monotonic()-started)
        result['valid_scan_sequence']=bool(result.get('valid_scan_sequence') and not failed and hci_seen)
        events=[json.loads(line) for line in (folder/'host-events.jsonl').read_text().splitlines()]
        result['hci_by_host_receive_time']=summarize_hci(events,token)
        result['hci_measurement_clean']=all(s['matched']>0 and not any(s['anomalies'].values())
                                          for s in result['hci_by_host_receive_time'].values())
        (folder/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
        if result.get('valid_scan_sequence'):
            for mode in ['ON','OFF']:
                s=result['statistics'][mode]['RX']
                if s['intervals']:print(f"扫描 {mode}: RX 6–10ms={s['pct6_10']:.1f}%, 30–50ms={s['pct30_50']:.1f}%, {s['intervals']} 个间隔")
        bundle=folder.with_suffix('.zip')
        with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED) as z:
            for f in folder.iterdir():
                if f.is_file():z.write(f,f.name)
        print('完成。请提供这个文件：'+str(bundle),flush=True)
    return 1 if failed else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dongle-port',required=True);parser.add_argument('--right-port',required=True)
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    if os.path.realpath(args.dongle_port)==os.path.realpath(args.right_port):parser.error('两个端口必须不同')
    root=Path(__file__).resolve().parents[3]/'build/reports'
    output=args.output_dir or root/('radio-ab-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    sys.exit(run_capture(args.dongle_port,args.right_port,output))
