from pathlib import Path
from .mdict_query.mdict_query import IndexBuilder
from .dict_parser.manager import ParserManager


xsj_path = Path("./assets/xinshijirihan.mdx")
djs_path = Path("./assets/DJS.mdx")
moji_path = Path("./assets/MOJi辞書.mdx")


def preprocess_entry(entry):
    if "<link rel=" in entry:
        return ParserManager.remove_useless_part(entry)
    return entry


class DictHelper:
    def __init__(self):
        self.xsj = IndexBuilder(str(xsj_path))
        self.djs = IndexBuilder(str(djs_path))
        self.moji = IndexBuilder(str(moji_path))
        self.xsj_count = 0
        self.djs_count = 0
        self.moji_count = 0

        self._create_sqlite_if_not_exists(xsj_path, self.xsj)
        self._create_sqlite_if_not_exists(djs_path, self.djs)
        self._create_sqlite_if_not_exists(moji_path, self.moji)

    def _create_sqlite_if_not_exists(self, mdx_path, index_builder):
        sqlite_db_path = Path(str(mdx_path) + ".sqlite.db")
        if not sqlite_db_path.is_file():
            index_builder.make_sqlite()

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