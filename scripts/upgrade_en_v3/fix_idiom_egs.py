import json
from loguru import logger
from tqdm.contrib.concurrent import thread_map
from tqdm import tqdm

from src.utils import Recorder

logger.remove()
logger.add('fix_idiom_egs.log', format="{extra[id]} ----------------\n {extra[old]} \n->\n {extra[new]}", serialize=False)


recorder = Recorder()

def process(idiom):
    if idiom["examples"]:
        egs = json.loads(idiom["examples"])
        ori_egs = [eg for eg in egs if not eg.get("en_ai", False)]
        if len(egs) != len(ori_egs):
            # recorder.update_def_examples(idiom["id"], json.dumps(ori_egs, ensure_ascii=False))
            with logger.contextualize(id=idiom["id"], new=json.dumps(ori_egs, ensure_ascii=False, indent=4), old=json.dumps(egs, ensure_ascii=False, indent=4)):
                logger.info('')

def main():
    idioms = list(recorder.get_idioms())
    for idiom in tqdm(idioms):
        process(idiom)




if __name__ == '__main__':
    recorder.start()

    main()

    recorder.close()