import os
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
def upload_file(file):
    file_object = client.files.create(file=file, purpose="batch")
    return file_object.id
def list_file():
    return client.files.list()

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

def list_batch():
    return client.batches.list(limit=20)

def download_file(id, output):
    content = client.files.content(file_id=id)
    if not output.parent.is_dir():
        output.parent.mkdir()
    content.write_to_file(output)
def main():
    fn = 'rate0'
    # print(list_file())
    # print(del_file(''))
    # id = upload_file(Path('./batch') / 'rate0.jsonl')
    # bid = run_batch("file-batch-9dsPWUvbozkjrZfyZvpdhhBC")
    # print(get_batch(bid))
    # print(list_batch().model_dump_json(indent=4))
    download_file("file-batch_output-pRE95VbpNALxtdno7o88F0Mp", Path('./batch_results') / f'{fn}.jsonl')
    pass

if __name__ == '__main__':
    main()

