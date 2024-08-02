from pathlib import Path
import json
import sqlite3
from loguru import logger
from threading import Lock
from itertools import tee
from tqdm.contrib.concurrent import thread_map
import re

lock = Lock()

db_name = 'todos_en.db'
db_file = Path.cwd() / 'src' / 'assets' / db_name

class Recorder:
    _instance = None
    connection = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Recorder, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not db_file.is_file():
            self.init_db()

    def start(self):
        if not self.connection:
            self.connection = sqlite3.connect(db_file, check_same_thread=False)

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def init_db(self):
        with sqlite3.connect(db_file) as conn:
            c = conn.cursor()
            c.execute(
                '''
                CREATE TABLE todos
                (
                    id TEXT not null unique,
                    o TEXT
                )
            '''
            )

    def get_all(self):
        sql = '''
            SELECT *
            FROM todos
            ORDER BY RANDOM();
        '''

        cursor = self.connection.execute(sql)

        return iter(
            SQLResultIterator(cursor, ['id', 'o'])
        )

    def init_todos(self, main_db_file):
        print('init todos')
        main_connection = sqlite3.connect(main_db_file, check_same_thread=False)
        egs_sql = '''
            SELECT examples
            FROM defs as d
            WHERE d.examples IS NOT NULL
            ORDER BY RANDOM();
        '''
        egs_cursor = main_connection.execute(egs_sql)

        egs, egs_clone = tee(iter(SQLResultIterator(egs_cursor, ['examples'])))

        def reduce_pattern(input_string):
            pattern = re.compile(r'\b(\w+)(?:/\w+)+\b')

            def replace_match(match):
                return match.group(1)

            result = re.sub(pattern, replace_match, input_string)

            return result

        def simplify_eg(en):

            # "2 multiplied by 4 is/equals/makes 8."
            # ->
            # "2 multiplied by 4 is 8."
            if '/' in en:
                en = reduce_pattern(en)

            # "We’re well off for jobs around here (= there are many available)."
            # ->
            # "We’re well off for jobs around here."
            if '(' in en:
                en = re.sub(r'(\s*\(.+\))', '', en)

            return en.strip()

        def insert_examples(egs_json):
            examples = json.loads(egs_json["examples"])
            updates = [(eg["name"], simplify_eg(eg["en"])) for eg in examples]
            sql = '''
                INSERT INTO todos(id,o)
                VALUES (?,?)
            '''
            self._transact(sql, updates, many=True)

        thread_map(insert_examples, egs, total=len(list(egs_clone)))


    def _transact(self, sql, vals, many=False):
        with lock:
            conn = self.connection

            try:
                cursor = conn.execute(sql, vals) if not many else conn.executemany(sql, vals)
                conn.commit()
                return cursor
            except Exception as e:
                logger.error(e)
                conn.rollback()
                return None

    def test_sql(self, sql):
        cursor = self.connection.execute(sql)
        return cursor.fetchall()


class SQLResultIterator:
    def __init__(self, cursor, fields):
        self.cursor = cursor
        self.fields = fields
        pass

    def __iter__(self):
        return self

    def __next__(self):
        row = self.cursor.fetchone()
        if not row:
            raise StopIteration
        return self._parse(row)

    def _parse(self, row):
        return {k: row[idx] for idx, k in enumerate(self.fields)}
