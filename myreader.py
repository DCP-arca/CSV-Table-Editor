import pandas as pd
target_csv = pd.read_csv('target.csv', encoding="euc-kr", sep="|", engine="pyarrow")
