import PyPDF2
import re

def examine_pdf_content(pdf_path):
    """Examine PDF content to understand the structure"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(reader.pages)} pages")
            print("=" * 80)
            
            # Extract first few pages to understand structure
            for page_num in range(min(3, len(reader.pages))):
                page = reader.pages[page_num]
                text = page.extract_text()
                print(f"\n--- PAGE {page_num + 1} ---")
                print(text[:1000])  # First 1000 characters
                print("...")
                
            # Look for year patterns
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            print("\n" + "=" * 80)
            print("YEAR PATTERNS FOUND:")
            years = re.findall(r'\b20(2[1-5])\b', full_text)
            year_counts = {}
            for year in years:
                year_counts[year] = year_counts.get(year, 0) + 1
            for year, count in sorted(year_counts.items()):
                print(f"  20{year}: {count} occurrences")
            
            print("\nSUBJECT PATTERNS:")
            # Look for common subject names
            subjects = ['BAHASA MELAYU', 'BAHASA INGGERIS', 'MATEMATIK', 'SAINS', 'SEJARAH', 
                       'PENDIDIKAN MORAL', 'FIZIK', 'KIMIA', 'BIOLOGI']
            
            for subject in subjects:
                if subject in full_text:
                    lines_with_subject = [line for line in full_text.split('\n') if subject in line]
                    print(f"\n{subject}:")
                    for i, line in enumerate(lines_with_subject[:3]):  # Show first 3 occurrences
                        print(f"  {i+1}: {line.strip()}")
            
            # Look for percentage patterns
            print("\nPERCENTAGE PATTERNS:")
            percentages = re.findall(r'\b\d+\.\d+%\b', full_text)
            print(f"Found {len(percentages)} percentages")
            print("Sample percentages:", percentages[:10])
            
            # Look for table-like structures
            print("\nTABLE-LIKE STRUCTURES:")
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                # Look for lines with multiple numbers (potential table rows)
                numbers = re.findall(r'\d+', line)
                if len(numbers) >= 3 and len(numbers) <= 6:
                    print(f"Line {i}: {line.strip()}")
                    if i > 100:  # Limit output
                        break
                        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    examine_pdf_content("Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025.pdf")
