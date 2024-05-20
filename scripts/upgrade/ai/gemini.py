import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)

with open('hint.txt', mode='r', encoding='utf-8') as f:
    content = f.read()

model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=content)

question = '''
1. "purr": to speak in a low and gentle voice, for example to show you are happy or satisfied, or because you want to attract sb or get them to do sth.
2. "●make a silk ˌpurse out of a sow's ˈear": to succeed in making sth good out of material that does not seem very good at all.
3. "puzzlement": a feeling of being confused because you do not understand sth.
4. "fudge": to avoid giving clear and accurate information, or a clear answer.
5. "full-scale": that is as complete and thorough as possible.
6. "gilt": a young female pig.
7. "genus": a group into which animals, plants, etc. that have similar characteristics are divided, smaller than a family and larger than a species.
8. "paltry": having no value or useful qualities.
9. "dig 'into sth": to start to eat food with enthusiasm.
'''
response = model.generate_content(question)
print(response.text)
print(response.usage_metadata)

