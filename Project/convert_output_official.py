import pandas as pd
from extract_transcription_translation import trans_df
from extract_chinese_pdf import sinonom_df

# Merge two dataframes by Page and Column
res_df = pd.merge(sinonom_df, trans_df, on=['Page', 'Column'], how='inner')

res_df.to_excel("final_df.xlsx", index=False)
print("Done!")

