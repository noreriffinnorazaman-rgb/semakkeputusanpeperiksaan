import PyPDF2

def read_pdf_raw(pdf_path):
    """Read the raw text from each page of the PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        print(f"PDF has {len(reader.pages)} pages\n")
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            print(f"{'='*80}")
            print(f"PAGE {page_num + 1}")
            print(f"{'='*80}")
            print(text)
            print()

if __name__ == "__main__":
    read_pdf_raw("Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025.pdf")
