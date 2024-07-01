from src.utils import Recorder, DictHelper
from src.dict_parser import ParserManager

dict_helper = DictHelper()
parser = ParserManager()

results = dict_helper.query_oaldpe('take')



result = parser.parse(results[0])

pass

