from pathlib import Path
import json
import sqlite3
from loguru import logger
from threading import Lock
from itertools import chain
from random import shuffle

lock = Lock()

db_name = 'upgrade.db'
db_file = Path.cwd() / 'src' / 'assets' / db_name

label_filter = '''
    WHERE labels=''
        OR (
            instr(labels, 'British English') > 0
            OR instr(labels, 'American English') > 0
            OR instr(labels, 'US English') > 0
        )
        OR (
            not instr(labels, 'Australian English') > 0
            and not instr(labels, 'New Zealand English') > 0
            and not instr(labels, 'Indian English') > 0
            and not instr(labels, 'African English') > 0
            and not instr(labels, 'Canadian English') > 0
            and not instr(labels, 'South-East Asian English') > 0
            and not instr(labels, 'Irish English') > 0
            and not instr(labels, 'Scottish English') > 0
            and not instr(labels, 'Welsh English') > 0
        )
'''

class Recorder:
    common_def_fields = ['id', 'cefr', 'labels', 'definition', 'def_cn', 'examples', 'variants', 'topic', 'score',
                         'reason']

    common_todo_def_fields = ['id', 'definition', 'def_cn', 'examples', 'variants', 'topic', 'score', 'reason']

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
            self.connection.execute('PRAGMA foreign_keys = ON;')

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

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
                    labels TEXT,
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
                        labels TEXT,
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
            c.execute(
                '''
                CREATE TABLE synonyms
                (
                    id TEXT not null,
                    overview TEXT,
                    overview_cn TEXT,
                    defs TEXT,
                    words TEXT
                )
            '''
            )
            c.execute(
                '''
                CREATE TABLE whichwords
                (
                    id TEXT not null,
                    overview TEXT,
                    overview_cn TEXT,
                    defs TEXT,
                    words TEXT
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
                json.dumps(d["examples"], ensure_ascii=False) if d["examples"] else None,
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
            VALUES(?,?,?,?,?,?,?)
        '''
        value = (
            entry_id,
            item["word"],
            item["dict_type"],
            f'{item["phonetics"][0]}=_={item["phonetics"][1]}',
            item["usage"],
            item["pos"],
            item["labels"]
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
            VALUES(?,?,?,?)
        '''
        value = (
            entry_id,
            item["word"],
            item["pos"],
            item["labels"]
        )
        cursor.execute(sql, value)

        self._save_defs(cursor, entry_id, item["defs"])

    def _save_phrvs(self, cursor, word, phrvs):
        if not phrvs:
            return
        for entries in phrvs:
            for entry in entries:
                self._save_phrv(cursor, word, entry)
    @logger.catch
    def _save_synonym_or_whichword(self, cursor, table, item):
        sql = f'''
            INSERT INTO {table}
            VALUES(?,?,?,?,?)
        '''
        value = (
            item["id"],
            item["overview"],
            item['overview_cn'],
            json.dumps(item['defs'], ensure_ascii=False) if item['defs'] else None,
            item['group']
        )
        cursor.execute(sql, value)

    def _save_synonyms(self, cursor, synonyms):
        if synonyms:
            for s in synonyms:
                self._save_synonym_or_whichword(cursor, 'synonyms', s)

    def _save_whichwords(self, cursor, whichwords):
        if whichwords:
            for w in whichwords:
                self._save_synonym_or_whichword(cursor, 'whichwords', w)

    @logger.catch
    def save(self, results):
        with lock:
            conn = self.connection

            try:
                for item in results:
                    self._save_word(conn.cursor(), item)
                    self._save_idioms(conn.cursor(), item["word"], item["idioms"])
                    self._save_phrvs(conn.cursor(), item["word"], item['phrases'])
                    self._save_synonyms(conn.cursor(), item["synonyms"])
                    self._save_whichwords(conn.cursor(), item["whichwords"])
                conn.commit()
            except Exception as e:
                logger.error(e)
                conn.rollback()

    def save_word_entry_only(self, word):
        with lock:
            conn = self.connection
            try:
                self._add_entry(conn.cursor(), word)
                conn.commit()
            except Exception as e:
                conn.rollback()

    def get_all(self):
        return chain(
            self.get_words(),
            self.get_idioms(),
            self.get_phrvs()
        )

    def get_words(self):
        sql = '''
            SELECT d.id, d.cefr, d.labels, d.definition, d.def_cn, d.examples, d.variants, d.topic, d.score, d.reason, words.word, words.phonetics, words.pos, words.labels AS e_labels, d.usage
            FROM defs AS d
                INNER JOIN entries
                ON d.entry_id = entries.id
                INNER JOIN words
                ON words.entry_id = entries.id
            WHERE d.def_cn!='' AND d.examples IS NOT NULL AND d.topic!='' AND d.score is NOT NULL AND d.reason is NOT NULL
            ORDER BY RANDOM();
        '''
        cursor = self.connection.execute(sql)

        return iter(SQLResultIterator(cursor, [*self.common_def_fields, 'word', 'phonetics', 'pos', 'e_labels', 'usage']))

    def get_idioms(self):
        sql = '''
            SELECT d.id, d.cefr, d.labels, d.definition, d.def_cn, d.examples, d.variants, d.topic, d.score, d.reason,
            CASE
                WHEN d.usage='' THEN idioms.usage
                WHEN d.usage!='' THEN d.usage
            END AS usage
            FROM defs AS d
                INNER JOIN entries
                ON d.entry_id = entries.id
                INNER JOIN idioms
                ON idioms.entry_id = entries.id
            WHERE d.def_cn!='' AND d.examples IS NOT NULL AND d.topic!='' AND d.score is NOT NULL AND d.reason is NOT NULL
            ORDER BY RANDOM();
        '''
        cursor = self.connection.execute(sql)
        return iter(SQLResultIterator(cursor, [*self.common_def_fields, 'usage']))

    def get_phrvs(self):
        sql = '''
            SELECT d.id, d.cefr, d.labels, d.definition, d.def_cn, d.examples, d.variants, d.topic, d.score, d.reason, phrvs.pos, phrvs.labels as e_labels
            CASE
                WHEN d.usage='' THEN phrvs.usage
                WHEN d.usage!='' THEN d.usage
            END AS usage 
            FROM defs AS d
                INNER JOIN entries
                ON d.entry_id = entries.id
                INNER JOIN phrvs
                ON phrvs.entry_id = entries.id
            WHERE d.def_cn!='' AND d.examples IS NOT NULL AND d.topic!='' AND d.score is NOT NULL AND d.reason is NOT NULL
            ORDER BY RANDOM();
        '''
        cursor = self.connection.execute(sql)

        return iter(SQLResultIterator(cursor, [*self.common_def_fields, 'pos', 'e_labels', 'usage']))

    def get_synonyms(self):
        sql = '''
            SELECT *
            FROM synonyms
            GROUP BY id
            ORDER BY RANDOM()
        '''

        cursor = self.connection.execute(sql)
        return iter(SQLResultIterator(cursor, ['id', 'overview', 'overview_cn', 'defs', 'words']))


    def get_whichwords(self):
        sql = '''
            SELECT *
            FROM whichwords
            GROUP BY id
            ORDER BY RANDOM()
        '''

        cursor = self.connection.execute(sql)
        return iter(SQLResultIterator(cursor, ['id', 'overview', 'overview_cn', 'defs', 'words']))

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

    def _update_def(self, def_id, col, val):
        sql = f'''
            UPDATE defs
            SET {col}=?
            WHERE id=?
        '''
        self._transact(sql, (val, def_id))


    def update_def_topic(self, def_id, topics):
        self._update_def(def_id, 'topic', topics)

    def update_def_examples(self, def_id, examples_json):
        self._update_def(def_id, 'examples', examples_json)

    def update_def_cn(self, def_id, def_cn):
        self._update_def(def_id, 'def_cn', def_cn)

    def update_def_rate(self, def_id, score, reason):
        sql = f'''
            UPDATE defs
            SET score=?, reason=?
            WHERE id=?
        '''
        self._transact(sql, (score, reason, def_id))

    def update_synonyms_defs(self, synonym_id, defs):
        sql = f'''
            UPDATE synonyms
            SET defs=?
            WHERE id=?
        '''
        self._transact(sql, (json.dumps(defs, ensure_ascii=False), synonym_id))

    def update_whichword_defs(self, whichword_id, defs):
        sql = f'''
            UPDATE whichwords
            SET defs=?
            WHERE id=?
        '''
        self._transact(sql, (json.dumps(defs, ensure_ascii=False), whichword_id))

    def get_todos(self):
        return chain(
            self.get_todo_words(),
            self.get_todo_idioms(),
            self.get_todo_phrvs()
        )

    def get_todo_words(self):
        sql = f'''
            SELECT d.id, d.definition, d.def_cn, d.examples, d.variants, d.topic, d.score, d.reason, words.word, d.usage 
            FROM (
                SELECT * from defs
                {label_filter}
            ) AS d
            INNER JOIN entries
            ON d.entry_id = entries.id
            INNER JOIN (
                SELECT * from words
                {label_filter}
            ) as words
            ON words.entry_id = entries.id
            WHERE d.def_cn='' OR d.examples IS NULL OR d.topic='' OR (d.score is NULL AND d.reason is NULL)
            ORDER BY (
                CASE WHEN d.def_cn='' THEN 1 ELSE 0 END +
                CASE WHEN d.examples IS NULL THEN 1 ELSE 0 END +
                CASE WHEN d.topic='' THEN 1 ELSE 0 END +
                CASE WHEN d.score IS NULL THEN 1 ELSE 0 END +
                CASE WHEN d.reason IS NULL THEN 1 ELSE 0 END
            ) ASC, RANDOM();
        '''
        cursor = self.connection.execute(sql)

        return iter(SQLResultIterator(cursor, [*self.common_todo_def_fields, 'word', 'usage']))

    def get_todo_idioms(self):
        sql = f'''
            SELECT d.id, d.definition, d.def_cn, d.examples, d.variants, d.topic, d.score, d.reason, 
            CASE
                WHEN d.usage='' THEN idioms.usage
                WHEN d.usage!='' THEN d.usage
            END AS usage
            FROM (
                SELECT * from defs
                {label_filter}
            ) AS d
                INNER JOIN entries
                ON d.entry_id = entries.id
                INNER JOIN idioms
                ON idioms.entry_id = entries.id
            WHERE d.def_cn='' OR d.examples IS NULL OR d.topic='' OR (d.score is NULL AND d.reason is NULL)
            ORDER BY (
                CASE WHEN d.def_cn='' THEN 1 ELSE 0 END +
                CASE WHEN d.examples IS NULL THEN 1 ELSE 0 END +
                CASE WHEN d.topic='' THEN 1 ELSE 0 END +
                CASE WHEN d.score IS NULL THEN 1 ELSE 0 END +
                CASE WHEN d.reason IS NULL THEN 1 ELSE 0 END
            ) ASC, RANDOM();
        '''
        cursor = self.connection.execute(sql)
        return iter(SQLResultIterator(cursor, [*self.common_todo_def_fields, 'usage']))

    def get_todo_phrvs(self):
        sql = f'''
            SELECT d.id, d.definition, d.def_cn, d.examples, d.variants, d.topic, d.score, d.reason,
            CASE
                WHEN d.usage='' THEN phrvs.usage
                WHEN d.usage!='' THEN d.usage
            END AS usage 
            FROM (
                SELECT * from defs
                {label_filter}
            ) AS d
            INNER JOIN entries
            ON d.entry_id = entries.id
            INNER JOIN (
                SELECT * from phrvs
                {label_filter}
            ) as phrvs
            ON phrvs.entry_id = entries.id
            WHERE d.def_cn='' OR d.examples IS NULL OR d.topic='' OR (d.score is NULL AND d.reason is NULL)
            ORDER BY (
                CASE WHEN d.def_cn='' THEN 1 ELSE 0 END +
                CASE WHEN d.examples IS NULL THEN 1 ELSE 0 END +
                CASE WHEN d.topic='' THEN 1 ELSE 0 END +
                CASE WHEN d.score IS NULL THEN 1 ELSE 0 END +
                CASE WHEN d.reason IS NULL THEN 1 ELSE 0 END
            ) ASC, RANDOM();
        '''
        cursor = self.connection.execute(sql)

        return iter(SQLResultIterator(cursor, [*self.common_todo_def_fields, 'usage']))

    def test_sql(self, sql):
        cursor = self.connection.execute(sql)
        return cursor.fetchall()

    def correct_usages(self, todos):
        updates = [(t["change"][1], t["id"]) for t in todos]
        sql = '''
            UPDATE defs
            SET usage=?
            WHERE id=?
        '''
        self._transact(sql, updates, many=True)

    def clear_rate(self, todos):
        updates = [(t["id"],) for t in todos]
        sql = '''
            UPDATE defs
            SET score=NULL, reason=NULL
            WHERE id=?
        '''
        self._transact(sql, updates, many=True)


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
