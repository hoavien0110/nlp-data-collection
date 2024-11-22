import fitz  # PyMuPDF

def pdf_to_png(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    
    # Lặp qua từng trang trong PDF
    for page_number in range(pdf_document.page_count):
        if (page_number >= 1 and page_number <= 4)  or (page_number % 2 == 0 and page_number):
            continue
        # Lấy trang hiện tại
        page = pdf_document.load_page(page_number)
        
        # Chuyển trang thành hình ảnh với độ phân giải (dpi) mong muốn
        pix = page.get_pixmap(dpi=150)
        
        # Đặt tên tệp PNG
        output_file = f"{output_folder}/page_{page_number + 1}.png"
        
        # Lưu hình ảnh dưới dạng PNG
        pix.save(output_file)
        
    # Đóng tệp PDF
    pdf_document.close()
    print(f"PDF đã được chuyển đổi thành công. Các trang đã lưu trong thư mục: {output_folder}")

# Gọi hàm
pdf_path = "E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\PDF\\VoHoangHoaVien_Manh Tu C6.pdf"  # Đường dẫn đến tệp PDF
output_folder = "E:\\study 7\\NLP\\Thuc_hanh\\nlp-data-collection\\NotResized"  # Thư mục chứa ảnh xuất ra
pdf_to_png(pdf_path, output_folder)
