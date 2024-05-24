import os
import google.generativeai as genai
from pathlib import Path
cwd = Path('./ai')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)

with open(cwd / 'hint.txt', mode='r', encoding='utf-8') as f:
    content = f.read()

model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=content)


def test():
    resp = model.generate_content('write a story about magic in 50 words')
    print(resp.text)

def construct_question(words):
    question = ''
    for idx, (word, definition) in enumerate(words):
        question += f'{idx+1}. "{word}": {definition}\n'
    return question


def rate(words):
    question = construct_question(words)
    response = model.generate_content(question)
    return response


