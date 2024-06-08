import difflib
from pathlib import Path
from collections import defaultdict
import logging
import json
import pickle

from upgrade_ja.dict_lookup import lookup
from upgrade_ja.dict_parser.manager import ParserManager
from upgrade_ja.dict_parser.guanyongju import CommonIdiomsIterator

from upgrade_ja.utils import is_hiragana, is_onaji, remove_punctuations, is_katakana, is_cjk

logger = logging.getLogger(__name__)
logging.basicConfig(filename="common_idiom_correct.log",
        level=logging.DEBUG,
        format="%(message)s",
                    encoding='utf-8'
                    )

parser = ParserManager()
html_dir = Path('./upgrade_ja/assets/idioms')
common_cns_file = Path('./upgrade_ja/assets/idioms/common_cn_character.txt')
rare_cns_file = Path('./upgrade_ja/assets/idioms/rare_cn_character.txt')
common_jps_file = Path('./upgrade_ja/assets/idioms/common_ja_character.txt')
similar_cn_jp_file = Path('./upgrade_ja/assets/idioms/similar_cn_jp.txt')

idioms = CommonIdiomsIterator(html_dir)

similar_cn_jp_mapping_blacklist = ['屦', '谂', '桩', '锫', '挥', '划', '缂', '拟']

manual_mapping_html = {
    '囫': "囲",
    '扳': "扱",
    '逯': "遊",
    '络': "絡",
    '颏': "顔",
    '浞': '況',
    '顷': '頃',
    '骢': '験',
    '姊': '姉',
    '徵': '徴',
    '榨': '搾',
    '賬': '賑',
    '犏': '犠',
    '桩': '粧',
    '瘛': '癒',
    '馱': '駄',
    '苤': "葷",
    '迕': "辻",
    '癎': '癪',
    '窬': '窓',
    '僦': '傑',
    '俱': '倶',
    '囝': '図',
    '宓': '実',
    '庀': '広',
    '捋': '採',
    '拚': '抜',
    '搿': '挙',
    '俅': '働',
    '耵': '恥',
    '綦': '線',
    '撙': '揃',
    '迤': '込',
    '庥': '応',
    '陴': '隠',
    '雒': '雑',
    '擤': '擡',
    '汊': '沢',
    '跗': '跡',
    '屦': '屍',
    '呋': '咲',
    '谂': '誌',
    '佾': '伝',
    '疰': '痒',
    '廑': '廃',
    '嘌': '喫',
    '砹': '砲',
    '阊': '闇',
    '唿': '唸',
    '焓': '煙',
    '泫': '滝',
    '锫': '鎮',
    '烀': '焼',
    '湄': '涙',
    '溻': '漏',
    '搌': '拵',
    '侔': '併',
    '妒': '妬',
    '仨': '仮',
    '挹': '払',
    '洄': '沖',
    '癍': '癪',
    '橐': '棄',
    '缂': '綯',
    "笾": '篠',
    "鳎": "鰯",
    "缏": "総",
    "蓠": "薬",
    "脶": "脇",
    "囵": "団",
    "阃": "闘",
    "讵": "証",
    "阌": "関",
    "哝": "呪",
    "涞": "満",
    "钱": "銭",
}
manual_mapping_defs = {
    '见': '見',
    '蓝': '藍',
    '书': '書',
    '张': '張',
    '难': '難',
    '规': '規',
    '喻': '喩',
    '拟': '似',
    '骂': '罵',
    "伪": "偽",
    "别": "別",
    "绳": "縄",
    "剂": "剤",
    "纵": "縦",
    "觉": "覚",
    '仿': '倣',
}

manual_mapping = {**manual_mapping_defs, **manual_mapping_html}

# 有多个汉字的情况，固定选一个
duplicate_kanji_map = {
    # こめ　-> 込|籠
    '迤': "込",
    '揚': "上",
    '葳': "倉",
    '掊': "択",
}

def get_mapping():
    duplicates = defaultdict(list)
    mapping = set()
    white_list = ['一', '人', '付', '搔']

    for idiom in idioms:
        word = idiom['word']
        kanji = idiom['kanji']

        result = lookup(kanji, word, mode='KJE')
        if result:
            continue
        result = lookup(word, None, mode='KJE')
        if result:
            parsed = parser.parse(result)

            c_kanji = parsed['kanji']
            if not c_kanji:
                continue
            if '【' in c_kanji:
                c_kanji = c_kanji[1:-1]

            if len(c_kanji) != len(kanji):
                continue

            diff_list = [li for li in difflib.ndiff(kanji, c_kanji) if li[0] != ' ']
            if not diff_list:
                continue

            diff_tuples = []

            # ['- 步', '+ 歩', '- 步', '+ 歩']
            if diff_list[0][0] != diff_list[1][0]:
                for i in range(0, len(diff_list), 2):
                    diff_tuples.append((diff_list[i][2], diff_list[i+1][2]))

            else:
                delta = int(len(diff_list) / 2)
                for i, start in enumerate(diff_list):
                    if start[0] == '+':
                        break
                    pair = diff_list[i+delta]
                    diff_tuples.append((start[2], pair[2]))

            for cn, ja in diff_tuples:
                if is_hiragana(ja) or is_hiragana(cn) or is_onaji(ja) or is_onaji(cn):
                    continue

                if cn in white_list:
                    continue
                if cn in duplicate_kanji_map:
                    ja = duplicate_kanji_map.get(cn)

                if (cn, ja) not in mapping:
                    duplicates[cn].append((kanji, c_kanji))

                mapping.add((cn, ja))

    for key, value in duplicates.copy().items():
        if len(value) <= 1:
            duplicates.pop(key)
    return mapping, duplicates

def split_mapping(mapping):
    with open(common_cns_file, mode='r', encoding='utf-8') as f:
        common_cns = [s.strip() for s in f.readlines()]
    with open(common_jps_file, mode='r', encoding='utf-8') as f:
        common_jps = [s.strip()[-1] for s in f.readlines()]

    html_mapping = set()
    entry_mapping = set()

    for item in mapping:
        if item[0] in common_cns or item[0] in common_jps:
            entry_mapping.add(item)
        else:
            html_mapping.add(item)

    return html_mapping, entry_mapping

def get_raw_mapping_manually(knowns):
    raw_map = defaultdict(set)
    similar_dict = {}
    white_list = ['瘦', '搔']
    similar_cn_jp_dict = {}
    with open(common_jps_file, mode='r', encoding='utf-8') as f:
        common_jps = [s.strip()[-1] for s in f.readlines()]
    with open(similar_cn_jp_file, mode='r', encoding='utf-8') as f:
        for s in f.readlines():
            s = s.strip()
            similar_cn_jp_dict[s[0]] = s[-1]

    for idiom in idioms:
        if idiom["is_redirect"]:
            continue
        kanji = idiom["kanji"]
        word = idiom["word"]
        definition = idiom["definition"]
        examples = idiom["examples"]
        text = "".join(filter(None, [definition, *[eg["ja"] for eg in examples]]))
        for c in remove_punctuations(text):
            if c in manual_mapping:
                continue
            if is_cjk(c) and c not in knowns and c not in common_jps and c not in white_list:
                string = text.replace(c, '〇')

                if not raw_map[c]:
                    raw_map[c].add('0' + kanji)
                    raw_map[c].add('0' + word)
                raw_map[c].add(string)

    for c, v in raw_map.copy().items():
        if c in similar_cn_jp_dict and c not in similar_cn_jp_mapping_blacklist:
            logger.info(f'{c} -> {similar_cn_jp_dict[c]}')
            logger.info(str(v))
            raw_map.pop(c)
            similar_dict[c] = similar_cn_jp_dict[c]

    for c, v in raw_map.copy().items():
        if len(v) <= 3:
            raw_map.pop(c)

    return raw_map, similar_dict


mapping, duplicates = get_mapping()

html_mapping, entry_mapping = split_mapping(mapping)

raw_mapping, similar_mapping = get_raw_mapping_manually([c for c,_ in html_mapping])


def mapping_to_dict(mapping):
    result = {}
    for c, j in mapping:
        result[c] = j
    return result



# 全文通用
with open(html_dir / 'correct_mapping_html.pkl', mode='wb') as f:
    pickle.dump({**(mapping_to_dict(html_mapping)), **manual_mapping_html}, f)

# 仅日文释义、日文例句通用
with open(html_dir / 'correct_mapping_defs.pkl', mode='wb') as f:
    pickle.dump({**similar_mapping, **manual_mapping_defs}, f)

pass