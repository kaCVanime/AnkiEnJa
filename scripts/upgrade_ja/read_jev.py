import pandas
import random


jev = pandas.read_excel("JEV.xlsx", header=1, index_col=0)
data = jev[["標準的な表記", "読み"]]
d1 = data.drop_duplicates(subset=["標準的な表記", "読み"])

d1_list = d1.to_numpy().tolist()
print(['揺する', 'ユスル'] in d1_list)
# for i in random.sample(d1_list, 5):
#     print(d1_list[i])

