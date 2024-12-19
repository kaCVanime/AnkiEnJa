import json
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from pathlib import Path
from collections import defaultdict
from loguru import logger

cwd = Path(__file__).parent

logger.add(cwd / 'warn.log', level='WARNING')

mp = cwd / 'models/deberta-v3-large-zeroshot-v2.0'
topics_fp = cwd / 'topics/WikipediaCategoriesFiltered.txt'
oald_topics_fp = cwd / 'topics/OALD.txt'

tokenizer = AutoTokenizer.from_pretrained(mp)
model = AutoModelForSequenceClassification.from_pretrained(mp)
config = AutoConfig.from_pretrained(mp)
ask = pipeline('zero-shot-classification', model=model, tokenizer=tokenizer, device=0)

# Health and fitness -> { Health: Health and fitness, fitness: Health and fitness }
def build_descriptors():
    with open(topics_fp, mode='rt', encoding='utf-8') as f:
        return {k.strip().capitalize(): domain.strip() for domain in f for k in domain.strip().split(' and ')}


descriptors = build_descriptors()
topics = list(descriptors.keys())

def get_oald_descriptors(descriptors):
    with open(oald_topics_fp, mode='rt', encoding='utf-8') as f:
        d = {k.strip().capitalize(): domain.strip() for domain in f for k in domain.strip().split(' and ')}
    dkeys = [a.lower() for a in descriptors.keys()]
    for k in d:
        if k.lower() in dkeys:
            d.pop(k)

    return d

oald_descriptors = get_oald_descriptors(descriptors)
descriptors = { **descriptors, **oald_descriptors }
topics = [*topics, *oald_descriptors.keys()]

def classify(s, word=None):
    threshold = 0.88
    c_thres = 0.6

    results = ask(s, candidate_labels=topics, hypothesis_template='The topic of this definition is about {}', multi_label=True)
    # results = ask(s, candidate_labels=topics, multi_label=True)
    ts = results["scores"]
    ls = results["labels"]

    r = defaultdict(float)
    for i in range(7):
        r[descriptors[ls[i]]] += ts[i]

    ss = sorted(r.items(), key=lambda item: item[1], reverse=True)

    p = []
    for topic, score in ss:
        if score > threshold:
            p.append(topic)

    if not p:
        for topic, score in ss[:2]:
            if score > c_thres:
                m = logger.warning if score > 0.75 else logger.error
                m('{}({}) -> {}', topic, score, s)
                p.append(topic)

    return p


if __name__ == '__main__':
    # classify("solar panel: a piece of equipment, often on the roof of a building, that uses light and heat energy from the sun to produce hot water and electricity.")
    # classify("high-powered: having a lot of power and influence; full of energy.")
    # classify("high-powered: very powerful")
    # classify("high-powered: (of people) having a lot of power and influence; full of energy.")
    # classify("labrador: a large dog that can be yellow, black or brown in colour, often used by blind people as a guide")
    # classify("disc: a CD or DVD")
    # classify("70")
    # classify('to hit something many times in order to break it into smaller pieces')
    # classify('a piece of furniture for one person to sit on, with a back, a seat and four legs')
    # classify('broil means to become or make somebody become very hot')
    # classify("the fact of being strict or severe")
    # classify("a container on your desk for letters that are waiting to be read or answered")
    # classify("a formal talk that a person gives to an audience")
    # classify("a quality of beauty, style and feeling")
    # classify("to hit somebody very hard so that they fall down")
    # classify("if a building is bombed out, it has been destroyed by bombs")
    #
    # result = classify("high-powered: having a lot of power and influence; full of energy.")
    pass
