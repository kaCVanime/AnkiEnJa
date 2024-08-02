from pathlib import Path
import pickle
from upgrade_ja.dict_parser.guanyongju import Writer


html_dir = Path('./upgrade_ja/assets/idioms')
output_dir = Path('./upgrade_ja/assets/idioms_corrected_v2')

correct_mapping_html_file = Path('./upgrade_ja/assets/idioms/correct_mapping_html.pkl')
correct_mapping_defs_file = Path('./upgrade_ja/assets/idioms/correct_mapping_defs.pkl')



correct_mapping_html = {}
correct_mapping_defs = {}

if correct_mapping_html_file.is_file():
    with open(correct_mapping_html_file, "rb") as f:
        correct_mapping_html = pickle.load(f)
if correct_mapping_defs_file.is_file():
    with open(correct_mapping_defs_file, "rb") as f:
        correct_mapping_defs = pickle.load(f)


writer = Writer(html_dir)

writer.run(output_dir, correct_mapping_html,  correct_mapping_defs)



