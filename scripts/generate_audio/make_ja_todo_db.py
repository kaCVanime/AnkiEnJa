import json
import re

from src.utils import anki_invoke, JARecorder
from tqdm.contrib.concurrent import thread_map
from tqdm import tqdm
from loguru import logger

recorder = JARecorder()

logger.remove()
logger.add('make_ja_todo_db.log', level='INFO')


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

# filter uncommon kanji
def filter_kanji(kanji):
    if not kanji:
        return ''
    kanji = kanji.strip()
    if kanji.startswith('【'):
        kanji = kanji[1:-1]

    # Wilhelm Konrad Röntgen
    if re.search(r"^[a-zA-Z;\d.'・()\- \u0080-\u00ff\u0370-\u03ff\u0100-\u017f]+$", kanji):
        return ''

    # フランス appliqué
    if 'フランス ' in kanji or 'ポルトガル ' in kanji or '英 ' in kanji or 'ドイツ ' in kanji or 'アラビア ' in kanji or 'オランダ ' in kanji or 'ヒンディー ' in kanji:
        return ''

    ks = kanji.split('／')
    if len(ks) >= 1:
        ks = kanji.split('┊')

    # ▽: 不常用的读音
    # ×: 不常用汉字
    # ＝: 熟字训且不常用汉字
    common = [k for k in ks if '▽' not in k and '×' not in k and '＝' not in k]

    if not common:
        return ''

    result = re.sub(r'[×▽－＝]', '', common[0])

    # 挙（げ）句 -> 挙げ句
    result = re.sub(r'[()（）]', '', result)

    # 現す〔現わす〕 -> 現わす
    if match := re.search(r'〔(.+?)〕', result):
        result = match.group(1)

    return result


def convert_eg(e, word, kanji):
    name = e["name"]
    ja = e["ja"]

    # エッセンス
    # バニラ-－
    # 香草精
    if '-－' in ja:
        ja = ja.replace('-－', word)

    # 合う
    # いくつもの川が－・って大河となる
    # 几条河汇合成为一条大江
    if '－・' in ja:
        pass

    if '－' in ja:
        ja = ja.replace('－', kanji or word)

    return {
        "name": name,
        "ja": ja
    }
def convert_examples(examples, word, kanji):
    return [convert_eg(e, word, kanji) for e in examples]
def update_db(eg_group):
    return recorder.insert_examples(eg_group[0])

def main():
    print('fetching notes...')
    egs = []
    nids = anki_invoke('findNotes', query='deck:KJXP::Read')
    nids = nids[:10]

    for nid in tqdm(nids):
        fields = get_note_fields(nid)
        if fields["examples"]:
            examples = json.loads(fields["examples"])
            kanji = filter_kanji(fields["kanji"])
            egs.append([convert_examples(examples, fields["word"], kanji)])

    pass

    print('adding to db...')
    thread_map(update_db, egs)

    pass


if __name__ == '__main__':
    recorder.start()
    main()
    recorder.close()