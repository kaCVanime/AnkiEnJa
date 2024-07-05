from pathlib import Path
import json
import sqlite3
from loguru import logger
from threading import Lock

lock = Lock()

db_name = 'upgrade.db'
db_file = Path.cwd() / 'src' / 'assets' / db_name


class Recorder:
    def __init__(self):
        if not db_file.is_file():
            self.init_db()
        self.connection = None

    def start(self):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        cur = self.connection.cursor()
        cur.execute('PRAGMA foreign_keys = ON;')
    def close(self):
        self.connection.close()

    def init_db(self):
        with sqlite3.connect(db_file) as conn:
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            c.execute(
                '''
                CREATE TABLE entries
                (
                    id INTEGER PRIMARY KEY,
                    word TEXT
                )
            '''
            )
            c.execute(
                '''
                CREATE TABLE words
                (
                    entry_id INTEGER,
                    word TEXT not null,
                    dict_type TEXT,
                    phonetics TEXT,
                    usage TEXT,
                    pos TEXT,
                    FOREIGN KEY(entry_id) REFERENCES entries(id) ON DELETE CASCADE 
                )
            '''
            )
            c.execute(
                '''
                    CREATE TABLE idioms
                    (
                        entry_id INTEGER,
                        usage TEXT not null,
                        FOREIGN KEY(entry_id) REFERENCES entries(id) ON DELETE CASCADE 
                    )
                '''
            )
            c.execute(
                '''
                    CREATE TABLE phrvs
                    (
                        entry_id INTEGER,
                        usage TEXT not null,
                        pos TEXT,
                        FOREIGN KEY(entry_id) REFERENCES entries(id) ON DELETE CASCADE 
                    )
                '''
            )
            c.execute(
                '''
                CREATE TABLE defs
                (
                    id TEXT not null unique,
                    entry_id INTEGER,
                    cefr TEXT,
                    usage TEXT,
                    labels TEXT,
                    definition TEXT not null,
                    def_cn TEXT,
                    examples TEXT,
                    variants TEXT,
                    topic TEXT,
                    score INTEGER,
                    reason TEXT,
                    FOREIGN KEY(entry_id) REFERENCES entries(id) ON DELETE CASCADE 
                )
            '''
            )

    def get_keys(self):
        sql = '''
            SELECT DISTINCT word
            FROM entries
        '''
        with sqlite3.connect(db_file) as conn:
            res = conn.execute(sql)
        return [row[0] for row in res.fetchall()]

    def get(self):
        pass

    def remove(self, word):
        sql = '''
            DELETE FROM entries
            WHERE word=(?);
        '''
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute('PRAGMA foreign_keys = ON;')
            cur.execute(sql, (word,))

    def _add_entry(self, cursor, word):
        sql='''
          INSERT INTO entries(word)
          VALUES(?)
        '''
        cursor.execute(sql, (word,))
        return cursor.lastrowid

    def _save_defs(self, cursor, entry_id, defs):
        if not defs:
            return
        sql = '''
            INSERT INTO defs(entry_id,id,cefr,usage,labels,definition,def_cn,examples,variants,topic)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        '''
        values = [
            (
                entry_id,
                d["id"],
                d["cefr"],
                d["usage"],
                d["labels"],
                d["definition"],
                d["def_cn"],
                json.dumps(d["examples"]),
                d["variants"],
                d["topic"]
            )
            for d in defs
        ]
        cursor.executemany(sql, values)

    def _save_word(self, cursor, item):
        entry_id = self._add_entry(cursor, item['word'])
        sql ='''
            INSERT INTO words
            VALUES(?,?,?,?,?,?)
        '''
        value = (
            entry_id,
            item["word"],
            item["dict_type"],
            f'{item["phonetics"][0]}=_={item["phonetics"][1]}',
            item["usage"],
            item["pos"],
        )
        cursor.execute(sql, value)

        self._save_defs(cursor, entry_id, item["defs"])



    def _save_idiom(self, cursor, entry_id, item):
        sql = '''
            INSERT INTO idioms
            VALUES(?,?)
        '''
        value = (
            entry_id,
            item["usage"]
        )
        cursor.execute(sql, value)
        self._save_defs(cursor, entry_id, item["defs"])

    def _save_idioms(self, cursor, word, idioms):
        if not idioms:
            return
        for d in idioms:
            entry_id = self._add_entry(cursor, word)
            self._save_idiom(cursor, entry_id, d)

    def _save_phrv(self, cursor, word, item):
        entry_id = self._add_entry(cursor, word)
        sql ='''
            INSERT INTO phrvs
            VALUES(?,?,?)
        '''
        value = (
            entry_id,
            item["word"],
            item["pos"]
        )
        cursor.execute(sql, value)

        self._save_defs(cursor, entry_id, item["defs"])

    def _save_phrvs(self, cursor, word, phrvs):
        if not phrvs:
            return
        for entries in phrvs:
            for entry in entries:
                self._save_phrv(cursor, word, entry)


    def save(self, results):
        with lock:
            conn = self.connection

            try:
                for item in results:
                    self._save_word(conn.cursor(), item)
                    self._save_idioms(conn.cursor(), item["word"], item["idioms"])
                    self._save_phrvs(conn.cursor(), item["word"], item['phrases'])
                conn.commit()
            except Exception as e:
                conn.rollback()

    def save_word_entry_only(self, word):
        with lock:
            conn = self.connection
            try:
                self._add_entry(conn.cursor(), word)
                conn.commit()
            except Exception as e:
                conn.rollback()
