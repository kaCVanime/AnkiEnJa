from pathlib import Path
from mdict_query.mdict_query import IndexBuilder


xsj_path = Path('./assets/xinshijirihan.mdx')
djs_path = Path('./assets/DJS.mdx')
moji_path = Path('./assets/MOJi辞書.mdx')

class DictHelper:
    def __init__(self):
        self.xsj = IndexBuilder(str(xsj_path))
        self.djs = IndexBuilder(str(djs_path))
        self.moji = IndexBuilder(str(moji_path))

        self._create_sqlite_if_not_exists(xsj_path, self.xsj)
        self._create_sqlite_if_not_exists(djs_path, self.djs)
        self._create_sqlite_if_not_exists(moji_path, self.moji)

    def _create_sqlite_if_not_exists(self, mdx_path, index_builder):
        sqlite_db_path = Path(str(mdx_path) + '.sqlite.db')
        if not sqlite_db_path.is_file():
            index_builder.make_sqlite()

    def query_all(self, word, select=None):
        query_methods = [self.query_xsj, self.query_djs, self.query_moji]
        if select:
            query_methods = query_methods[:select]
        results = []
        for method in query_methods:
            results = method(word)
            if results:
                return results
        return results

    def query_best(self, word, select):
        query_methods = [self.query_xsj, self.query_djs, self.query_moji]
        query_methods = query_methods[:select]
        results = []
        for method in query_methods:
            results.append(method(word))
        return min(results, key=len)

    def query_xsj(self, word):
        return self.xsj.mdx_lookup(word)

    def query_djs(self, word):
        return self.djs.mdx_lookup(word)

    def query_moji(self, word):
        return self.moji.mdx_lookup(word)

