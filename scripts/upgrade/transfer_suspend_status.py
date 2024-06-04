import logging

from anki_connect import invoke as anki_invoke
from tqdm import tqdm


logger = logging.getLogger(__name__)


def run():
    src_nids = anki_invoke("findCards", query="deck:KEXP::Read")
    for nid in tqdm(src_nids):
        if anki_invoke("suspended", card=nid):
            infos = anki_invoke("cardsInfo", cards=[nid])
            card = infos[0]
            target_nids = anki_invoke(
                "findCards",
                query=f"deck:KEXP::Write id:{card['fields']['id']['value']}",
            )
            anki_invoke("suspend", cards=target_nids)


if __name__ == "__main__":
    run()
