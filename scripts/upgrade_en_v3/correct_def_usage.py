
from loguru import logger
from pathlib import Path
from tqdm.contrib.concurrent import thread_map
from tqdm import tqdm

from src.utils import Recorder, lookup
from src.dict_parser import ParserManager
from collections import defaultdict

log_path = Path('./src/logs')
log_path.mkdir(exist_ok=True)

logger.remove()
logger.add(log_path / 'correct_def_usage.log', level="INFO")

parser = ParserManager()

results_recorder = Recorder()


def normalize(s):
    return s.replace('·', '')

def get_words_with_usage():
    sql = '''
        SELECT d.id, d.cefr, d.topic, d.score, d.reason, d.usage, words.word 
        FROM defs AS d
            INNER JOIN entries
            ON d.entry_id = entries.id
            INNER JOIN words
            ON words.entry_id = entries.id
        WHERE d.usage!='' and d.usage IS NOT NULL
        ORDER BY d.id
    '''
    rows = results_recorder.test_sql(sql)

    fields = ['id', 'cefr', 'topic', 'score', 'reason', 'usage', 'word']

    row_objects = [
        {
            field: row[idx] if field != 'word' else normalize(row[idx])
            for idx, field in enumerate(fields)
        }
        for row in rows
    ]

    row_objects_group_by_word_dict = defaultdict(list)
    for obj in row_objects:
        row_objects_group_by_word_dict[obj["word"]].append(obj)

    return row_objects_group_by_word_dict



def get_todos(word_list):
    b1 = ['republican', 'follow-up', 'em', 'start-up', 'trade-off', 'cut-off', 'close-up', 'warm-up', 'cover-up', 'stand-up', 'run-down', 'drop-off', 'run-up', 'Labour', 'break-in', 'sit-up', 'carry-on', 'stand-in', 'run-in', 'shake-up', 'blow-up', 'layoff']
    b2 = ['tear', 'Bible', 'OK', 'makeup', 'Olympics', 'setup', 'cleanup', 'lineup', 'northwestern', 'fund-raiser', 'Freeman', 'runoff', 'payoff', 'breakup', 'best-seller', 'kinda', 'Pentagon', 'wake-up', 'kickoff', 'take-out', 'time-out', 'goddamned', 'roundup', 'side-by-side', 'telecom', 'hangout', 'reverend', 'holdout', 'e-mailed', 'on-the-job']
    blacklist=[*b1, *b2]
    # completed = [normalize(k) for k in results_recorder.get_keys()]
    completed = []
    todo = [w for w in word_list if w not in completed and w not in blacklist]
    return todo

def find_matches(results, rows):
    if not results or not rows:
        return []
    m = []
    r_dict = {}
    for entry in results:
        if entry["defs"]:
            for d in entry["defs"]:
                r_dict[d["id"]] = d

    for row in rows:
        if (rid := row["id"]) in r_dict and (r_usage := r_dict[rid]["usage"]) != row["usage"]:
            m.append({
                "id": rid,
                "change": (row["usage"], r_usage)
            })

    return m

# @logger.catch
def main():
    word_groups = get_words_with_usage()
    word_list = list(word_groups.keys())

    def f(word):
        results = lookup(word, word_list, save=False)
        rows = word_groups[word]

        todo_changes = find_matches(results, rows)
        if todo_changes:
            results_recorder.correct_usages(todo_changes)
            for to in todo_changes:
                logger.info("{}: {} -> {}", to["id"], to["change"][0], to["change"][1])

    thread_map(f, word_list)
    # for t in tqdm(word_list):
    #     f(t)



def test(word):
    word_list = get_words_with_usage()
    return lookup(word, word_list, save=False)

if __name__ == '__main__':
    results_recorder.start()
    main()

    results_recorder.close()
    pass
