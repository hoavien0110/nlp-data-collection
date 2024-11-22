import fitz
import pandas as pd

# Tạo DataFrame để lưu dữ liệu
sinonom_df = pd.DataFrame(columns=['Page', 'Column', 'Transcription'])


class PDFExtractor:
    def __init__(self, filename):
        self.filename = filename
        self.pdf_file = fitz.open(filename)

    def extract_transcription_info(self):
        """
        Extract font information from each text span in the PDF, 
        grouping sentences by font and aligning by columns.
        """
        global sinonom_df
        threshold = 10  # Ngưỡng độ lệch hoành độ để nhóm chữ cùng cột
        for page_index in range(len(self.pdf_file)):
            if (page_index >= 1 and page_index <= 4) or (page_index % 2 == 0 and page_index):
                continue

            page = self.pdf_file.load_page(page_index)
            dictionary_elements = page.get_text('dict')

            columns = []  # Danh sách để nhóm các cột

            for block in dictionary_elements['blocks']:
                if 'lines' not in block:
                    continue
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        if not text:
                            continue
                        bbox = span['bbox']
                        if bbox in [
                            (303.2900085449219, 37.560028076171875, 311.30584716796875, 48.60002517700195),
                            (300.4100036621094, 37.560028076171875, 314.06585693359375, 48.60002517700195),
                            (297.6499938964844, 37.560028076171875, 316.8258361816406, 48.60002517700195)
                        ]:
                            continue
                        font = span['font']
                        if font not in ['Calibri', 'TimesNewRomanPS-BoldMT', 'Calibri-Bold']:
                            x1 = bbox[0]

                            # Nhóm chữ theo cột
                            found = False
                            for column in columns:
                                if abs(column['x'] - x1) <= threshold:
                                    column['texts'].append((font, text, bbox))
                                    found = True
                                    break
                            if not found:
                                columns.append({'x': x1, 'texts': [(font, text, bbox)]})

            sorted_columns = sorted(columns, key=lambda col: col['x'], reverse=True)

            for col_idx, column in enumerate(sorted_columns, start=1):
                sorted_texts = sorted(column['texts'], key=lambda item: item[2][1])
                column_text = " ".join([text for _, text, _ in sorted_texts])

                sinonom_df = sinonom_df._append({
                    'Page': page_index,
                    'Column': col_idx - 1,
                    'Transcription': column_text
                }, ignore_index=True)




print("-------------------------------------------------------------------")
print("EXTRACTING INFORMATION FROM PDF")
filename = "E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\PDF\\VoHoangHoaVien_Manh Tu C6.pdf"
extractor = PDFExtractor(filename)
extractor.extract_transcription_info()
# extractor.extract_translation_text()

# Lưu DataFrames ra file CSV
# trans_df = pd.merge(transcription_df, translation_df, on=['Page', 'Column'], how='inner')
# trans_df.to_csv('E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\transcription_translation.csv', index=False)
print(sinonom_df)
sinonom_df.to_excel('E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\sinonom_df.xlsx', index=False)

print("-------------------------------------------------------------------")
