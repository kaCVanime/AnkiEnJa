from pathlib import Path
import pickle
from upgrade_ja.dict_parser.guanyongju import Writer


html_dir = Path('./upgrade_ja/assets/idioms')
output_dir = Path('./upgrade_ja/assets/idioms_corrected')

correct_mapping_entry_file = Path('./upgrade_ja/assets/idioms/correct_mapping_entry.pkl')
correct_mapping_html_file = Path('./upgrade_ja/assets/idioms/correct_mapping_html.pkl')
correct_mapping_defs_file = Path('./upgrade_ja/assets/idioms/correct_mapping_defs.pkl')

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
    '俱': '倶'
}
manual_mapping_entry = {
    '见': '見',
    '蓝': '藍',
    '书': '書',
    '张': '張',
    '难': '難',
    '规': '規',
    '喻': '喩',
    '拟': '似',
    '骂': '罵',
}
correct_mapping_entry = {}
correct_mapping_html = {}
correct_mapping_defs = {}
if correct_mapping_entry_file.is_file():
    with open(correct_mapping_entry_file, "rb") as f:
        correct_mapping_entry = pickle.load(f)
if correct_mapping_html_file.is_file():
    with open(correct_mapping_html_file, "rb") as f:
        correct_mapping_html = pickle.load(f)
if correct_mapping_defs_file.is_file():
    with open(correct_mapping_defs_file, "rb") as f:
        correct_mapping_defs = pickle.load(f)


writer = Writer(html_dir)

writer.run(output_dir, { **correct_mapping_html, **manual_mapping_html }, { **correct_mapping_entry, **manual_mapping_entry }, { **correct_mapping_defs, **manual_mapping_entry })



