content = open('main.py', 'r', encoding='utf-8').read()

replacements = [
    ('\u00f0\u009f\u0094 Scanning', 'Scanning'),
    ('\u00f0\u009f\u008c Building URL queue', 'Building URL queue'),
    ('\u00e2\u009c\u0085 Crawled:', '[ok] Crawled:'),
    ('\u00e2\u008f\u00ad Skipped:', '[skip] Skipped:'),
    ('\u00f0\u009f•·\u00ef\u00b8\u008f', '[spider]'),
    ('\u00f0\u009f\u0094\u0084 Crawled', 'Crawled'),
    ('\u00f0\u009f\u0093\u00a7 Found', 'Found'),
    ('\u00f0\u009f\u00a7\u00b9 Cleaned', 'Cleaned'),
    ('\u00e2\u009c\u0094\u00ef\u00b8\u008f Validated', 'Validated'),
    ('\u00e2\u0098\u0086 Selected', 'Selected'),
    ('\u00f0\u009f\u008e\u00af Bug bounty', 'Bug bounty'),
    ('\u00e2\u0084\u00b9\u00ef\u00b8\u008f No bounty', 'No bounty'),
]

import re
# Replace all non-ASCII emoji sequences with clean text
import re
def clean_emojis(text):
    # Remove emoji/unicode garbage - keep only ASCII printable + common chars
    result = ''
    i = 0
    while i < len(text):
        c = text[i]
        if ord(c) < 128:
            result += c
        else:
            # Skip non-ASCII chars that are part of broken emoji sequences
            result += ''
        i += 1
    return result

# Find all send( lines and clean them
lines = content.split('\n')
new_lines = []
for line in lines:
    if 'send(f"' in line or "send(f'" in line:
        cleaned = clean_emojis(line)
        new_lines.append(cleaned)
    else:
        new_lines.append(line)

new_content = '\n'.join(new_lines)
open('main.py', 'w', encoding='utf-8').write(new_content)
print('DONE - cleaned all send() lines')
