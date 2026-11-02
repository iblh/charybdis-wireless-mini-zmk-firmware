#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import re
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('right_keymap',HERE/'prepare_right_only_keymap.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
original=(HERE.parents[1]/'config/keymaps/touch_modes.keymap').read_text()
result=p.transform(original)
def layers(text):
    return {name: re.findall(r'&\w+[^&]*',body) for name,body in
            re.findall(r'(\w[\w-]*) \{ display-name = "[^"]+"; bindings = <(.*?)>;',text,re.S)}
before,after=layers(original),layers(result)
assert before.keys()==after.keys() and len(before)==9
for name in before:
    if name!='nav': assert before[name]==after[name]
changes={i:(b.strip(),a.strip()) for i,(b,a) in enumerate(zip(before['nav'],after['nav'])) if b!=a}
assert changes=={11:('&kp DEL','&mkp MB2'),23:('&kp ENTER','&mo SCROLL'),
                 35:('&kp RSHFT','&mo SLOW'),39:('&kp ENTER','&mkp MB1')}
assert '&thumb NAV SPACE' in result
try:p.transform(result)
except ValueError:pass
else:raise AssertionError('double application should fail closed')
print('PASS right-only mouse: exactly four NAV bindings change; all base modes and eight other layers unchanged; double application rejected')
if len(sys.argv)>1:
    import pickle
    sys.path.insert(0,str(HERE.parents[1]/'zephyr/scripts/dts/python-devicetree/src'))
    with (Path(sys.argv[1])/'zephyr/edt.pickle').open('rb') as f: edt=pickle.load(f)
    bindings=edt.get_node('/keymap/nav').props['bindings'].val
    for index,node,parameter in [(11,'mouse_key_press',2),(23,'momentary_layer',8),
                                 (35,'momentary_layer',7),(39,'mouse_key_press',1)]:
        binding=bindings[index]
        assert binding.controller.path.endswith('/'+node)
        assert list(binding.data.values())==[parameter]
    print('PASS compiled DTS: right-only left/right click and SCROLL/SLOW layer IDs')
