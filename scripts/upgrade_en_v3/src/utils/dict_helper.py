from pathlib import Path
from ..mdict_query.mdict_query import IndexBuilder


current_file_folder = Path(__file__).parent

oaldpe_path = Path.cwd() / 'src' / "assets/oaldpe.mdx"


def preprocess_entry(entry):
    return entry


class DictHelper:
    def __init__(self):
        self.oaldpe = IndexBuilder(str(oaldpe_path))

        self._create_sqlite_if_not_exists(oaldpe_path, self.oaldpe)


    def _create_sqlite_if_not_exists(self, mdx_path, index_builder):
        sqlite_db_path = Path(str(mdx_path) + ".sqlite.db")
        if not sqlite_db_path.is_file():
            index_builder.make_sqlite()

    def get_mdx_keys(self, mode):
        raise NotImplementedError

    def query_oaldpe(self, word):
        results = self.oaldpe.mdx_lookup(word)
        result = list(filter(None, [preprocess_entry(e) for e in results]))
        return result
