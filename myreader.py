import pandas as pd
target_csv = pd.read_csv('result.csv', encoding="euc-kr", sep="|", engine="pyarrow")

print(target_csv["select"].describe())