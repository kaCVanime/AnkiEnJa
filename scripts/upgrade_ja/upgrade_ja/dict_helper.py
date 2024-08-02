from pathlib import Path
from .mdict_query.mdict_query import IndexBuilder
from .utils import import_from

current_file_folder = Path(__file__).parent

xsj_path = current_file_folder / "assets/xinshijirihan.mdx"
djs_path = current_file_folder / "assets/DJS.mdx"
moji_path = current_file_folder / "assets/MOJi辞書.mdx"
kje_path = current_file_folder / "assets/広辞苑.mdx"
jlpt_path = current_file_folder / "assets/JLPTGrammar.mdx"


def preprocess_entry(entry):
    ParserManager = import_from("upgrade_ja.dict_parser.manager", "ParserManager")
    if "<link rel=" in entry:
        return ParserManager.remove_useless_part(entry)
    return entry


class DictHelper:
    def __init__(self):
        self.xsj = IndexBuilder(str(xsj_path))
        self.djs = IndexBuilder(str(djs_path))
        self.moji = IndexBuilder(str(moji_path))
        self.kje = IndexBuilder(str(kje_path))
        self.jlpt = IndexBuilder(str(jlpt_path))
        self.xsj_count = 0
        self.djs_count = 0
        self.moji_count = 0

        self._create_sqlite_if_not_exists(xsj_path, self.xsj)
        self._create_sqlite_if_not_exists(djs_path, self.djs)
        self._create_sqlite_if_not_exists(moji_path, self.moji)
        self._create_sqlite_if_not_exists(kje_path, self.kje)
        self._create_sqlite_if_not_exists(jlpt_path, self.jlpt)


    def _create_sqlite_if_not_exists(self, mdx_path, index_builder):
        sqlite_db_path = Path(str(mdx_path) + ".sqlite.db")
        if not sqlite_db_path.is_file():
            index_builder.make_sqlite()

    def get_mdx_keys(self, mode):
        if mode == 'JLPT':
            return self.jlpt.get_mdx_keys()
        raise NotImplementedError

    def query_all(self, word, start=None, end=None):
        query_methods = [self.query_xsj, self.query_djs, self.query_moji]
        query_methods = query_methods[start:end]
        results = []
        for method in query_methods:
            results = method(word)
            if results:
                return results
        return results

    def query_best(self, word, start=None, end=None):
        query_methods = [self.query_xsj, self.query_djs, self.query_moji]
        query_methods = query_methods[start:end]
        results = []
        for method in query_methods:
            results.append(method(word))
        return min(results, key=len)

    def query_xsj(self, word):
        results = self.xsj.mdx_lookup(word)
        result = list(filter(None, [preprocess_entry(e) for e in results]))
        if len(result):
            self.xsj_count += 1
        return result

    def query_djs(self, word):
        results = self.djs.mdx_lookup(word)
        result = list(filter(None, [preprocess_entry(e) for e in results]))
        if len(result):
            self.djs_count += 1
        return result

    def query_moji(self, word):
        results = self.moji.mdx_lookup(word)
        result = list(filter(None, [preprocess_entry(e) for e in results]))
        if len(result):
            self.moji_count += 1
        return result

    def query_kje(self, word):
        results = self.kje.mdx_lookup(word)
        result = list(filter(None, [preprocess_entry(e) for e in results]))
        return result

    def query_jlpt(self, word):
        return self.jlpt.mdx_lookup(word)