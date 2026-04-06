content = open('app/page.js', 'r', encoding='utf-8').read()

fixes = [
    ('\u00f0\u009f\u0094', 'Starting scan for'),
    ('\u00f0\u009f\u008c', 'Connecting to backend...'),
    ('\u00f0\u009f\u0093\u00a1', 'Sending crawl request...'),
]

import re

def clean_emojis(text):
    result = ''
    for c in text:
        if ord(c) < 128:
            result += c
    return result

lines = content.split('\n')
new_lines = []
for line in lines:
    if 'addLog(' in line:
        new_lines.append(clean_emojis(line))
    else:
        new_lines.append(line)

open('app/page.js', 'w', encoding='utf-8').write('\n'.join(new_lines))
print('DONE')
