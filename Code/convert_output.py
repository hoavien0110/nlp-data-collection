import pandas as pd
import json
import xlsxwriter

class LabelProcessor:
    def __init__(self, ocr_df, trans_df):
        merge_df = pd.merge(ocr_df, trans_df, on=['Page', 'Column'], how='inner')
        self.quoc_ngu_groundtruth = merge_df['Transcription']
        self.df = pd.DataFrame({
            "Page": merge_df['Page'],
            "Column": merge_df['Column'],
            "transcription": merge_df['OCR'],
            "Points": merge_df['Points'],
            "quoc_ngu_groundtruth": merge_df['Transcription'],

        })
        self.df_final = None
        self.df.to_csv("E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\initial_df.csv", index=False)

    def transform_df_before_compare(self):
        self.df['quoc_ngu_groundtruth'] = self.quoc_ngu_groundtruth
        self.df['Âm Hán Việt'] = self.quoc_ngu_groundtruth
        # self.df['quoc_ngu_groundtruth'] = self.df['quoc_ngu_groundtruth'].apply(lambda x: x[:-1].replace(':', '').replace('.', '').replace(',', '').lower())
        self.df['quoc_ngu_groundtruth'] = self.df['quoc_ngu_groundtruth'].apply(
            lambda x: ''.join([char for char in x if not char.isdigit()])  # Remove digits
            .replace(':', '')
            .replace('.', '')
            .replace(',', '')
            .replace('?', '')
            .strip() 
            .lower()
        )
        self.df['transcription_list'] = self.df['transcription'].apply(list)
        self.df['quoc_ngu_groundtruth_list'] = self.df['quoc_ngu_groundtruth'].apply(lambda x: list(x.split(' ')))
        self.df.to_csv("E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\transformed_df.csv", index=False)

    def create_color_and_ID(self, alignment_processor):
        self.df['colors'] = self.df.apply(lambda row: alignment_processor.get_color(row), axis=1)
        # self.df['ppp'] = self.df['Page'].str.split('.').str[0].str.split('_').str[1]
        # self.df['ss'] = self.df['column'] * 2 - self.df['row'] % 2
        self.df['ID'] = self.df['Page']

    def get_final_dataframe(self):
        self.df_final = pd.DataFrame({
            "ID": self.df['ID'],
            "Image Box": self.df['Points'],
            "SinoNom char": self.df['transcription'],
            "Âm Hán Việt": self.df['Âm Hán Việt'],
            "Colors": self.df['colors']
        })

    def export_to_excel(self, filename='output.xlsx'):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()

        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        headers = ['ID', 'Image Box', 'SinoNom char', 'Âm Hán Việt']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        color_map = {'black': '#000000', 'blue': '#0000FF', 'red': '#FF0000'}
        default_font = 'Nom Na Tong'

        for idx, row in self.df_final.iterrows():
            worksheet.write(idx + 1, 0, row['ID'])
            worksheet.write(idx + 1, 1, str(row['Image Box']))
            worksheet.write(idx + 1, 3, row['Âm Hán Việt'])

            rich_text_1 = []
            
            for char1, color in zip(row['SinoNom char'], row['Colors']):
                color_hex = color_map.get(color, '#000000')
                cell_format = workbook.add_format({'font_color': color_hex, 'font_name': default_font})
                rich_text_1.append(cell_format)
                rich_text_1.append(char1)

            worksheet.write_rich_string(idx + 1, 2, *rich_text_1)

        workbook.close()


class AlignmentProcessor:
    def __init__(self):
        self.df_SinoNom = pd.read_excel("E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\SinoNom_similar_Dic.xlsx")
        self.df_QuocNgu = pd.read_excel("E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\QuocNgu_SinoNom_Dic.xlsx")

    def get_intersection(self, char1, char2):
        S1 = self.df_SinoNom[self.df_SinoNom['Input Character'] == char1]['Top 20 Similar Characters']
        if len(S1) == 0:
            S1 = [char1]
        else:
            S1 = eval(S1.values[0]) + [char1]
        S2 = self.df_QuocNgu[self.df_QuocNgu['QuocNgu'] == char2]['SinoNom'].to_list()
        intersection = [char for char in S1 if char in S2]
        return (1, intersection[0], len(intersection)) if intersection else (0, 0, 0)

    def Levenshtein_alignment(self, str1, str2):
        n, m = len(str1), len(str2)
        dp = [[i + j if i * j == 0 else 0 for j in range(m + 1)] for i in range(n + 1)]

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                equal, _, _ = self.get_intersection(str1[i - 1], str2[j - 1])
                dp[i][j] = dp[i - 1][j - 1] if equal else min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1]) + 1

        i, j = n, m
        alignment_str1, alignment_str2, colors = [], [], []
        while i > 0 or j > 0:
            equal, _, length = self.get_intersection(str1[i - 1], str2[j - 1])
            if i > 0 and j > 0 and equal > 0:
                colors.append('blue' if length > 1 else 'black')
                alignment_str1.append(str1[i - 1])
                alignment_str2.append(str2[j - 1])
                i, j = i - 1, j - 1
            elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                colors.append('red')
                alignment_str1.append(str1[i - 1])
                alignment_str2.append('-')
                i -= 1
            else:
                alignment_str1.append('-')
                alignment_str2.append(str2[j - 1])
                j -= 1

        return colors[::-1]

    def get_color(self, row):
        return self.Levenshtein_alignment(row['transcription_list'], row['quoc_ngu_groundtruth_list'])
    
from extract_transcription_translation import trans_df
from extract_SinoNom import ocr_df

alignment_processor = AlignmentProcessor()
label_processor = LabelProcessor(ocr_df, trans_df)
label_processor.transform_df_before_compare()
label_processor.create_color_and_ID(alignment_processor)
label_processor.get_final_dataframe()
label_processor.export_to_excel('output.xlsx')

