import json
from itertools import chain
from tqdm import tqdm
from loguru import logger
from src.utils import Recorder
from src.anki.anki_connect import invoke as anki_invoke

results_recorder = Recorder()

logger.remove()
logger.add('update_phrv_idioms_rate1.log', level='INFO')


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

def get_note_tags(nid):
    note = get_note(nid)
    return note["tags"]

def get_frequency(score):
    if score >= 95:
        return ['K_1_required']
    elif score >= 85:
        return ['K_2_daily']
    elif score > 50:
        return ['K_3_usual']
    else:
        return ['K_4_rare']

@logger.catch
def update_rate(nid, todo):
    fields = get_note_fields(nid)
    reason = todo["reason"] or ""
    if fields["brief"] == reason:
        return

    old_tags = get_note_tags(nid)
    new_tags = [t for t in old_tags if not t.startswith('K_')]
    new_tags.extend(get_frequency(todo["score"]))

    logger.info("{}-------------------".format(nid))
    logger.info("tag: {} -> {}".format(','.join(old_tags), ','.join(new_tags)))
    logger.info("brief: {} -> {}".format(fields["brief"], reason))

    new_fields = {
            "brief": reason
        }
    if '+' in fields["word"]:
        logger.info("word: {} -> {}".format(fields["word"], todo["usage"]))
        new_fields["word"] = '~ ' + todo["usage"]

    note = {
        "id": nid,
        "fields": new_fields,
        "tags": new_tags
    }
    anki_invoke('updateNote', note=note)
def main():
    results_recorder.start()
    todos = list(chain(results_recorder.get_phrvs(), results_recorder.get_idioms()))

    for todo in tqdm(todos):
        try:
            nids = anki_invoke("findNotes", query=f'deck:KEXP2 id:{todo["id"]}')
            assert len(nids) == 2

            for nid in nids:
                update_rate(nid, todo)

        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    main()