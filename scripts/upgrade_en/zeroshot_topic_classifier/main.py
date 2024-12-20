import json
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from pathlib import Path
from collections import defaultdict, Counter
from functools import reduce
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

def build_descriptors(fp):
    with open(fp, mode='rt', encoding='utf-8') as f:
        d = defaultdict(set)
        for domain in f:
            dom = domain.strip()
            for k in dom.split(' and '):
                d[k.strip().capitalize()].add(dom.capitalize())
        return d



descriptors = build_descriptors(topics_fp)

def add_oald_descriptors(descriptors):
    d = build_descriptors(oald_topics_fp)
    for k, v in d.items():
        descriptors[k] = descriptors[k].union(v)

add_oald_descriptors(descriptors)
topics = list(descriptors.keys())

def get_best_origin_topics(cls_results, descriptors, s):
    threshold = 0.9
    c_thres = 0.65

    scores = defaultdict(float)
    for label, score in cls_results:
        domains = descriptors[label]
        for domain in domains:
            scores[domain] += score

    deduplicated = {}
    for label, score in scores.items():
        if score not in deduplicated or len(label) < len(deduplicated[score]):
            deduplicated[score] = label
    items = [(label, score) for score, label in deduplicated.items()]

    topics = sorted(items, key=lambda item: item[1], reverse=True)

    results = []
    for i in range(5):
        label, score = topics[i]
        if score > threshold:
            results.append(topics[i])
        else:
            break

    if not results:
        for i in range(2):
            label, score = topics[i]
            if score > c_thres:
                # m = logger.warning if score > 0.75 else logger.error
                m = logger.warning
                m('{}({}) -> {}', label, score, s)
                results.append(topics[i])

    return results


def classify(s, word=None):
    answers = ask(s, candidate_labels=topics, hypothesis_template='The domain of the definition is {}', multi_label=True)
    # results = ask(s, candidate_labels=topics, multi_label=True)
    scores = answers["scores"]
    labels = answers["labels"]

    results = get_best_origin_topics(
        [
            (labels[i], scores[i])
            for i in range(50)
        ],
        descriptors,
        s
    )

    return [r[0] for r in results]


def test():
    test_inputs = [
        # '"solar panel" means "a piece of equipment, often on the roof of a building, that uses light and heat energy from the sun to produce hot water and electricity."',
        # '"high-powered" means "(of people) having a lot of power and influence; full of energy."',
        # '"labrador" means "a large dog that can be yellow, black or brown in colour, often used by blind people as a guide"',
        # '"disc" means "a CD or DVD"',
        # '"seventy" means "70"',
        # '"press" means "a piece of equipment that is used for creating pressure on things, to make them flat or to get liquid from them"',
        # '"broil" means "to become or make somebody become very hot"'
        "a piece of equipment, often on the roof of a building, that uses light and heat energy from the sun to produce hot water and electricity.",
        "(of people) having a lot of power and influence; full of energy.",
        "a large dog that can be yellow, black or brown in colour, often used by blind people as a guide",
        "a CD or DVD",
        "70",
        "a piece of equipment that is used for creating pressure on things, to make them flat or to get liquid from them",
        "to become or make somebody become very hot"
    ]
    results = [
        {
            's': s,
            'r': classify(s)
        } for s in test_inputs
    ]
    pass


if __name__ == '__main__':
    test()
    # classify('(Social issues) the process or result of making somebody feel as if they are not important and cannot influence decisions or events; the fact of putting somebody in a position in which they have no power')
    # classify('"shower" means "to give somebody a lot of something". Example: "He showered her with gifts."')
    # classify('"press" means "a piece of equipment that is used for creating pressure on things, to make them flat or to get liquid from them". Example: a trouser press.')
    # classify('"broil" means "to become or make somebody become very hot". Example: They lay broiling in the sun.')
    # classify('"broil" means "to become or make somebody become very hot". Example: They lay broiling in the sun.')
    # classify('"broil" means "to become or make somebody become very hot"')
    # classify('"boom" means "a loud deep sound"')
    # classify('"iraqi" means "(a person) from Iraq"')
    # test(test_inputs)
    pass
