#!/usr/bin/env python3
"""Optional right-half mouse access in NAV; preserve all base modes and other layers."""
import argparse
from pathlib import Path
import re


def transform(text):
    section = re.search(r'(nav \{ display-name = "NAV"; bindings = <)(.*?)(>;)\s*\};', text, re.S)
    if not section:
        raise ValueError('Expected NAV layer')
    body = section.group(2)
    matches = list(re.finditer(r'&\w+[^&]*', body))
    if len(matches) != 41:
        raise ValueError('Expected 41 physical positions')
    replacements = {11: ('&kp DEL', '&mkp MB2'), 23: ('&kp ENTER', '&mo SCROLL'),
                    35: ('&kp RSHFT', '&mo SLOW'), 39: ('&kp ENTER', '&mkp MB1')}
    for index in sorted(replacements, reverse=True):
        match = matches[index]
        before, after = replacements[index]
        value = match.group()
        if value.strip() != before:
            raise ValueError(f'Unexpected NAV position {index}: {value!r}')
        value = value.replace(before, after, 1)
        body = body[:match.start()] + value + body[match.end():]
    return text[:section.start(2)] + body + text[section.end(2):]


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.input.resolve() == a.output.resolve():
        raise ValueError('Do not overwrite the working keymap')
    result = transform(a.input.read_text())
    a.output.write_text(result)
