import os
import json
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
def upload_file(file):
    file_object = client.files.create(file=file, purpose="batch")
    return file_object.id
def list_file(purpose=None):
    l = client.files.list().data
    if purpose:
        return [f for f in l if f.purpose == purpose]
    return l

def get_file(id):
    return client.files.retrieve(file_id=id)

def del_file(id):
    return client.files.delete(file_id=id)

def run_batch(id):
    batch = client.batches.create(
        input_file_id=id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    return batch.id

def get_batch(id):
    return client.batches.retrieve(id)

def list_batch(status=None):
    data = client.batches.list(limit=20).data
    if status:
        return [d for d in data if d.status == status]
    return data

def download_file(id, output):
    content = client.files.content(file_id=id)
    if not output.parent.is_dir():
        output.parent.mkdir()
    content.write_to_file(output)

def check_custom_ids(p):
    with open(p, mode='r', encoding='utf-8') as f :
        lines = f.readlines()

    ids = []
    for l in lines:
        obj = json.loads(l)
        cid = obj["custom_id"]
        if cid in ids:
            raise Exception(f'duplicate: {cid}')
        else:
            ids.append(cid)
def upload_and_run(pattern='rate*.jsonl'):
    todos = sorted(Path('./batch').glob(pattern))
    for todo in todos:
        check_custom_ids(todo)
        id = upload_file(todo)
        run_batch(id)

def remove_todos():
    file_list = list_file('batch')
    for fb in file_list:
        del_file(fb.id)

def download_batch_outputs(output_path, created_at, prefix=''):
    if not output_path:
        output_path = Path('.')
    if not created_at:
        created_at = float('-inf')
    ids = [f.output_file_id for f in filter(lambda t: t.created_at >= created_at, list_batch(status='completed'))]
    for n in ids:
        p = output_path / f'{prefix}{n}.jsonl'
        if not p.is_file():
            download_file(n, p)

def main():
    # upload_and_run('translate*.jsonl')
    # bs = list_batch()
    download_batch_outputs(Path('./batch_results'), created_at=1734939868, prefix='translate-')

    # print(get_batch(bid))
    # print(list_batch().model_dump_json(indent=4))
    # download_file("file-batch_output-vu4fbUwHQZpXQmmaofwlf2GZ", Path('./batch_results') / f'test1w.jsonl')
    pass

if __name__ == '__main__':
    main()

