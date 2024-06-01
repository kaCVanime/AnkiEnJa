import re

word = 'test'

print(re.search(f"【{word}】", "apc"))
print(re.search(f"【{word}】", "【test】"))