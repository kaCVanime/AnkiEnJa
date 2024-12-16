import json
from transformers import ZeroShotClassificationPipeline, pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from pathlib import Path

mp = Path('./model')
tokenizer = AutoTokenizer.from_pretrained(mp)
model = AutoModelForSequenceClassification.from_pretrained(mp)
config = AutoConfig.from_pretrained(mp)
ask = pipeline('zero-shot-classification', model=model, tokenizer=tokenizer)

# Health and fitness -> { Health: Health and fitness, fitness: Health and fitness }
def build_descriptors():
    # with open('topics.json', mode='rt', encoding='utf-8') as f:
    #     return json.load(f)
    with open('BabelDomain.txt', mode='rt', encoding='utf-8') as f:
        return [s.strip() for s in f.readlines()]

topics = build_descriptors()

def classify(s):
    template = f"{s} {tokenizer.sep_token} The domain of the sentence is about "
    results = ask(template, candidate_labels=topics)
    ts = results["scores"]
    ls = results["labels"]
    mapped = { ls[i]: ts[i] for i, _ in enumerate(ts[:5]) }


    pass

if __name__ == '__main__':
    # classify("having a lot of power and influence; full of energy.")
    # classify("a large dog that can be yellow, black or brown in colour, often used by blind people as a guide")
    classify("hospital: a health facility where patients receive treatment.")
