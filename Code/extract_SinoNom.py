import pandas as pd
import json
import xlsxwriter

class LabelProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.df = None

    def process_label_file(self):
        def read_label_file(filename):
            with open(filename, "r", encoding='utf-8') as file:
                return [line.strip() for line in file]

        def extract_filenames_and_json(lines):
            filenames, json_lines = [], []
            for line in lines:
                pos = line.find('\t')
                pos2 = line.find('_')
                if pos != -1:
                    filenames.append(int(line[pos2+1:pos-4]) - 1)
                    json_lines.append(line[pos+1:])
            return filenames, json_lines

        def create_dataframe(filenames, json_lines):
            df = pd.DataFrame()
            for i, json_line in enumerate(json_lines):
                df_line = pd.DataFrame(json.loads(json_line))
                df_line['filename'] = filenames[i]
                df_line.drop(['difficult'], axis=1, errors='ignore', inplace=True)
                df_line = df_line[['filename'] + [col for col in df_line.columns if col != 'filename']]
                df = pd.concat([df, df_line], ignore_index=True)
            return df

        lines = read_label_file(self.filename)
        filenames, json_lines = extract_filenames_and_json(lines)
        self.df = create_dataframe(filenames, json_lines)
        self.df['points_str'] = self.df['points'].apply(lambda points: json.dumps(points))
        self.df.drop_duplicates(subset=['filename', 'transcription', 'points_str'], inplace=True)
        self.df.drop(columns=['points_str'], inplace=True)

    def sort_df(self):
        def get_center(points):

            return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)
        def combine_points(points_list):
            all_x = [point[0] for points in points_list for point in points]
            all_y = [point[1] for points in points_list for point in points]
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            return [(min_x, min_y), (max_x, max_y)]
        
        # Calculate centers for each cell
        self.df[['center_x', 'center_y']] = self.df['points'].apply(lambda points: pd.Series(get_center(points)))
        # self.df.to_excel('unsorted_df.xlsx')
        # Sort by center_x descending (right to left) and center_y descending (top to bottom)
        self.df = self.df.sort_values(by=['center_x', 'center_y'], ascending=[False, True])

        # Group by filename and then by columns with similar x-coordinates
        results = []
        grouped = self.df.groupby('filename')
        
        for filename, group in grouped:
            # Process each group
            column_buffer = []
            prev_x = None
            index = 0
            column_index = 1
            for _, row in group.iterrows():
                if prev_x is None or abs(prev_x - row['center_x']) > 10:
                    index += 1
                    # If there's accumulated text in column_buffer, flush it as a new column
                    if column_buffer:
                        # Sort column by center_y within this x grouping, to order top-to-bottom
                        column_buffer = sorted(column_buffer, key=lambda r: r['center_y'], reverse=False)
                        results.extend({
                            'filename': filename,
                            'column': column_index,
                            'row': row_index + 1,
                            'transcription': r['transcription'],
                            'center_x': r['center_x'],
                            'center_y': r['center_y'],
                            'points': r['points']
                        } for row_index, r in enumerate(column_buffer))
                        column_buffer = []
                        column_index += 1

                # Append current row to column_buffer
                column_buffer.append(row)
                prev_x = row['center_x']
            
            # Flush the last column buffer if not empty
            if column_buffer:
                column_buffer = sorted(column_buffer, key=lambda r: r['center_y'], reverse=True)
                results.extend({
                    'filename': filename,
                    'column': column_index,
                    'row': row_index + 1,
                    'transcription': r['transcription'],
                    'center_x': r['center_x'],
                    'center_y': r['center_y'],
                    'points': r['points']
                } for row_index, r in enumerate(column_buffer))

        # Create a DataFrame from sorted results and drop the center columns
        self.df = pd.DataFrame(results)
        self.df = self.df.sort_values(by=['filename', 'column', 'center_y'], ascending=[True, True, True])
        self.df['row'] = self.df.groupby(['filename', 'column']).cumcount() + 1
        # self.df.to_excel('sorted_df.xlsx')
        df_ocr_new = self.df.groupby(['filename', 'column']).apply(lambda x: pd.Series({
            'transcription': ''.join(x['transcription']),
            'points': combine_points(x['points'].tolist())
        })).reset_index()
        self.df = pd.DataFrame({
            'Page': df_ocr_new['filename'],
            'Column': df_ocr_new['column'] - 1,
            'OCR': df_ocr_new['transcription'],
            'Points': df_ocr_new['points']
        })
        self.df.to_csv('E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\Data\\ocr_df.csv', index=False)
        return self.df


label_processor = LabelProcessor("E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\ImagesFromPDF\\Label.txt")
label_processor.process_label_file()
ocr_df = label_processor.sort_df()
