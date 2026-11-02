#!/usr/bin/env python3
"""No devices: exercise real paired runner with simulated collector children."""
from pathlib import Path
import importlib.util,json,os,pty,subprocess,tempfile,tty,zipfile
SCRIPTS=Path(__file__).resolve().parents[2]/'docs/prospector-touch/scripts'
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
runner=load('radio',SCRIPTS/'capture-radio-ab.py')
collector=load('collector',SCRIPTS/'capture-right-profile.py')
master,slave=pty.openpty();tty.setraw(slave)
try:
 collector.scan_command(slave,'START',123)
 assert os.read(master,128)==b'!P8 START 123\n'
finally:os.close(master);os.close(slave)
# Synthetic clock and phase markers: incomplete windows/foreign runs must not count.
def logs(run):
 lines=[]
 for t in range(0,91):
  if t in [5,25,45,65]:
   n=[5,25,45,65].index(t)+1
   lines.append(f'[00:00:{t:02}.000,000] scan_ab: SCANAB run={run} event=PHASE phase={n} scan={int(n in [1,4])} links=1 err=0 t_ms={t*1000}')
  if t==85:lines.append(f'[00:01:25.000,000] scan_ab: SCANAB run={run} event=END phase=0 scan=1 links=1 err=0 t_ms=85000')
  if t%2:continue
  on=not 25<=t<65
  for stage in ['RX','USB']:
   lines.append(f'[00:{t//60:02}:{t%60:02}.000,000] pipe_profile: CAD stage={stage} frames=10 lt1=2 b1_6=0 b6_10={5 if on else 8} b10_14=0 b14_20=0 b20_30=0 b30_50={3 if on else 0} ge50=0 max_us=45000 max_under50_us=45000')
 return '\n'.join(lines)+'\n'
sample=logs(123);s=runner.summarize(sample,123)
assert s['valid_scan_sequence']
assert s['statistics']['ON']['RX']['pct30_50']==30
assert s['statistics']['OFF']['RX']['pct30_50']==0
assert not runner.summarize(sample,124)['valid_scan_sequence']
assert not runner.summarize(sample.replace('event=END','event=ABORT'),123)['valid_scan_sequence']
assert not runner.summarize(sample.replace('event=END phase=0 scan=1','event=END phase=0 scan=0'),123)['valid_scan_sequence']
# HCI alignment uses full host-receive windows with a conservative boundary gap.
events=[]
for n,t in [(1,5),(2,25),(3,45),(4,65)]:
 events.append(dict(role='dongle',host_elapsed_s=t,line=f'SCANAB run=123 event=PHASE phase={n} scan={int(n in [1,4])} links=1 err=0 t_ms={t*1000}'))
events.append(dict(role='dongle',host_elapsed_s=85,line='SCANAB run=123 event=END phase=0 scan=1 links=1 err=0 t_ms=85000'))
for t in [7,9,11,29,31,33]:
 events.append(dict(role='right',host_elapsed_s=t,line='HCI version=8 matched=2 avg_us='+str(10000 if t<25 else 1000)+' max_us=10000 orphan=0 overflow=0 reset=0 err=0 lt1=0 b1_6=0 b6_10=2 b10_14=0 b14_20=0 b20_30=0 b30_50=0 ge50=0'))
h=runner.summarize_hci(sorted(events,key=lambda e:e['host_elapsed_s']),123)
assert h['ON']['matched']==2 and h['ON']['weighted_avg_us']==10000
assert h['OFF']['matched']==4 and h['OFF']['weighted_avg_us']==1000
with tempfile.TemporaryDirectory() as td:
 root=Path(td);fake=root/'fake.py'
 fake.write_text('''import argparse,time\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument('--port');p.add_argument('--output',type=Path);p.add_argument('--seconds');p.add_argument('--scan-ab-run',type=int);a=p.parse_args()\n'''+repr('')+'\n'+f'''sample={sample!r}\n'''+'''text=sample.replace('run=123','run='+str(a.scan_ab_run)) if a.scan_ab_run else 'hci_profile: HCI version=8 tx=0\\n'\na.output.write_text(text);print(text,flush=True)\ntime.sleep(.1)\n''')
 real_popen=subprocess.Popen
 def fake_popen(command,**kwargs):
  command=list(command);command[1]=str(fake)
  return real_popen(command,**kwargs)
 runner.subprocess.Popen=fake_popen
 try:assert runner.run_capture('fake-dongle','fake-right',root/'result')==0
 finally:runner.subprocess.Popen=real_popen
 result=json.loads((root/'result/summary.json').read_text())
 assert result['valid_scan_sequence'] and result['hci_seen'] and not result['error']
 with zipfile.ZipFile(root/'result.zip') as z:
  assert set(z.namelist())=={'dongle.log','right.log','host-events.jsonl','summary.json'}
print('PASS paired collector: exact UART command, fresh run IDs, complete phase windows, restore validation, concurrent streams, summary and evidence ZIP; no physical ports opened')
