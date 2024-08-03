import re
from loguru import logger
def extract(fp, has_index):
    with open(fp, encoding='utf-8', mode='r') as f:
        lines = [s.strip() for s in f.readlines()]

    words = set()
    for r in lines:
        if not r:
            continue
        if has_index and re.search('^[A-Z]$', r):
            continue

        if r.startswith('*'):
            r = r[1:]
            r = r.strip()

        result = re.match(r"\b\w+\b([.' \-]\w*)*", r)

        w = result.group().strip()
        if w in words:
            logger.warning(f'Extractor: found duplicate word {w}')
        words.add(w)


    return words

