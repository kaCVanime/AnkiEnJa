from pathlib import Path
import sqlite3
from threading import Lock
from loguru import logger

lock = Lock()

class Recorder:
    _instance = None
    connection = None
    db_file = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Recorder, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not self.db_file.is_file():
            self.init_db()
        self.start()

    def start(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.execute('PRAGMA foreign_keys = ON;')

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            c.execute(
                '''
                CREATE TABLE examples
                (
                    id TEXT UNIQUE not null,
                    eg TEXT,
                    note_id TEXT not null
                )
            '''
            )
            c.execute(
                '''
                CREATE TABLE models
                (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    gpt_path TEXT,
                    sovits_path TEXT,
                    ref_path TEXT
                )
            '''
            )
            c.execute(
                '''
                CREATE TABLE audios
                (
                    id INTEGER PRIMARY KEY,
                    eg_id TEXT,
                    model_id INTEGER,
                    speed REAL,
                    path TEXT,
                    FOREIGN KEY(eg_id) REFERENCES examples(id),
                    FOREIGN KEY(model_id) REFERENCES models(id)
                )
            '''
            )

            c.execute(
                '''
                CREATE INDEX "idx_eg_id" ON "examples"
                (
                    "id"
                )
            '''
            )

    def is_examples_empty(self):
        sql = '''
            SELECT id
            FROM examples
        '''
        with sqlite3.connect(self.db_file) as conn:
            res = conn.execute(sql)
        return res.fetchone() is None

    def add_examples(self, nid, egs):
        sql = '''
            INSERT INTO examples
            VALUES(?,?,?)
        '''
        inserts = [(eg["name"], eg["eg"], nid) for eg in egs]
        self._transact(sql, inserts, many=True)
        pass

    def _transact(self, sql, vals, many=False):
        with lock:
            conn = self.connection

            try:
                if vals:
                    cursor = conn.execute(sql, vals) if not many else conn.executemany(sql, vals)
                else:
                    cursor = conn.execute(sql)
                conn.commit()
                return cursor
            except Exception as e:
                logger.error(e)
                conn.rollback()
                return None
class EnRecorder(Recorder):
    db_file = Path.cwd() / 'src' / 'assets' / 'en.db'
class JaRecorder(Recorder):
    db_file = Path.cwd() / 'src' / 'assets' / 'ja.db'
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
