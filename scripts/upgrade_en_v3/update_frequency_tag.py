
from tqdm import tqdm
from loguru import logger
from src.utils import Recorder
from src.anki.anki_connect import invoke as anki_invoke

results_recorder = Recorder()

logger.remove()
logger.add('update_frequency_tag.log', level='INFO')


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
    if score >= 90:
        return ['K_1_required']
    elif score >= 70:
        return ['K_2_daily']
    elif score > 40:
        return ['K_3_usual']
    else:
        return ['K_4_rare']

@logger.catch
def update_frequency_tag(nid, todo):
    new_f_tag = get_frequency(todo["score"])[0]
    old_tags = get_note_tags(nid)

    if new_f_tag in old_tags:
        return

    old_f_tag = next((t for t in old_tags if t.startswith('K_')), '')
    new_tags = [t for t in old_tags if not t.startswith('K_')]
    new_tags.append(new_f_tag)
    logger.info("{}: {} -> {}".format(nid, old_f_tag, new_f_tag))

    anki_invoke('updateNoteTags', note=nid, tags=new_tags)
def main():
    results_recorder.start()
    todos = list(results_recorder.get_all())

    for todo in tqdm(todos):
        if todo["score"] is None:
            continue
        try:
            nids = anki_invoke("findNotes", query=f'deck:KEXP2 id:{todo["id"]}')
            assert len(nids) == 2

            for nid in nids:
                update_frequency_tag(nid, todo)

        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    main()