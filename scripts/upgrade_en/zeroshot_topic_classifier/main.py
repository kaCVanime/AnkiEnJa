import json
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from pathlib import Path
from collections import defaultdict

mp = Path('./models/deberta-v3-large-zeroshot-v2.0')

tokenizer = AutoTokenizer.from_pretrained(mp)
model = AutoModelForSequenceClassification.from_pretrained(mp)
config = AutoConfig.from_pretrained(mp)
ask = pipeline('zero-shot-classification', model=model, tokenizer=tokenizer, device=0)

# Health and fitness -> { Health: Health and fitness, fitness: Health and fitness }
def build_leaf_descriptors():
    with open('./topics/Wikipedia.json', mode='rt', encoding='utf-8') as f:
        ts = json.load(f)
        return {k.strip().capitalize(): domain for domain in ts for k in domain.split('and')}

def build_babel_descriptors():
    with open('./topics/BabelDomains.txt', mode='rt', encoding='utf-8') as f:
        return {k.strip().capitalize(): domain.strip() for domain in f for k in domain.split('and')}

leaf_descriptors = build_leaf_descriptors()
leaf_topics = list(leaf_descriptors.keys())
babel_descriptors = build_babel_descriptors()
babel_topics = list(babel_descriptors.keys())
def classify(s, mode='Leaf'):
    descriptors = leaf_descriptors if mode == 'Leaf' else babel_descriptors
    topics = leaf_topics if mode == 'Leaf' else babel_topics
    threshold = 0.9 if mode == 'Leaf' else 0.8

    results = ask(s, candidate_labels=topics, hypothesis_template='The topic of the sentence is about {}', multi_label=True)
    # results = ask(s, candidate_labels=topics, multi_label=True)
    ts = results["scores"]
    ls = results["labels"]

    r = defaultdict(float)
    for i in range(8):
        r[descriptors[ls[i]]] += ts[i]

    p = []
    for topic, score in sorted(r.items(), key=lambda item: item[1], reverse=True):
        if score > threshold:
            p.append(topic)

    return p

def classify_all(s):
    return {
        "leaf": classify(s, mode='Leaf'),
        "babel": classify(s, mode='Babel')
    }


if __name__ == '__main__':
    # classify("solar panel: a piece of equipment, often on the roof of a building, that uses light and heat energy from the sun to produce hot water and electricity.")
    # classify("high-powered: having a lot of power and influence; full of energy.")
    # classify("high-powered: very powerful")
    # classify("high-powered: (of people) having a lot of power and influence; full of energy.")
    # classify("labrador: a large dog that can be yellow, black or brown in colour, often used by blind people as a guide")
    # classify("disc: a CD or DVD")
    # classify("hospital: a health facility where patients receive treatment.", mode='Babel')
    # result = classify_all("hospital: a health facility where patients receive treatment.")
    result = classify_all("high-powered: having a lot of power and influence; full of energy.")
    print(result)
    pass
