import pandas



jev = pandas.read_excel("JEV.xlsx", header=1, index_col=0)
data = jev[["標準的な表記", "読み"]]
print(data[data.duplicated(['標準的な表記', "読み"], keep=False)])
