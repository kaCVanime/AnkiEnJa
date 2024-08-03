from pathlib import Path
from extractor import extract
from loguru import logger

logger.remove()
logger.add('main.log')

def main():

    ori_path = Path.cwd() / 'origin'
    junior = extract(ori_path / '小学英语大纲词汇.txt', has_index=False)
    senior = extract(ori_path / '中考英语词汇表.txt', has_index=True)
    high = extract(ori_path / '高中.txt', has_index=False)
    cet4 = extract(ori_path / '四级.txt', has_index=True)
    cet6 = extract(ori_path / '六级.txt', has_index=False)
    prof = extract(ori_path / '专四专八.txt', has_index=False)

    dicts = [("小学", junior), ("初中", senior), ("高中", high), ("四级", cet4), ("六级", cet6), ("专四专八", prof)]
    ls = [z[1] for z in dicts]

    assets_path = Path.cwd() / 'assets'
    for idx, (name, wl) in enumerate(dicts):
        if idx == 0:
            continue

        abridged = wl
        for i in range(0, idx):
            abridged = abridged - ls[i]

        with open(assets_path / (name + '.txt'), encoding='utf-8', mode='w') as f:
            ordered = list(abridged)
            ordered.sort()
            f.writelines([(w + '\n') for w in ordered])

        print(f'{name}. Before: {len(wl)}; After: {len(abridged)}')

    pass

if __name__ == '__main__':
    main()