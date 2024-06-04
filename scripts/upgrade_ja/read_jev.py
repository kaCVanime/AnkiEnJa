import pandas
import random


jev = pandas.read_excel("./assets/JEV.xlsx", header=1, index_col=0)
data = jev[["標準的な表記", "読み"]]
d1 = data.drop_duplicates(subset=["標準的な表記", "読み"])

print(d1[d1["標準的な表記"].str.endswith("と")])
# print(d1[d1["標準的な表記"] == 'きんもうけ'])
