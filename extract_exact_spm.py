import PyPDF2
import re
import json

def extract_exact_spm_data(pdf_path):
    """Extract exact SPM data from the PDF with precise grade distributions"""
    
    data = {
        'spm_historical': {
            'years': [2021, 2022, 2023, 2024, 2025],
            'subjects': {},
            'overall_stats': {}
        }
    }
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            print("Extracting exact SPM data from PDF...")
            
            # Split by pages to better understand the structure
            pages = full_text.split('JABATAN PENDIDIKAN NEGERI PERLIS')[1:]
            
            # Process each page
            for page_idx, page_text in enumerate(pages):
                lines = page_text.split('\n')
                print(f"\n--- Processing Page {page_idx + 1} ---")
                
                # Look for subject data blocks
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Check for subject names
                    subjects = ['Bahasa Melayu', 'Bahasa Inggeris', 'Matematik', 'Sains', 
                               'Sejarah', 'Geografi', 'Pendidikan Moral', 'Fizik', 'Kimia', 'Biologi']
                    
                    for subject in subjects:
                        if subject in line and len(line) < 100:
                            print(f"Found subject: {subject}")
                            
                            # Look for the data associated with this subject
                            # The data pattern should be: grade numbers followed by year and GPMP
                            subject_data = {}
                            
                            # Search backwards and forwards for data patterns
                            search_start = max(0, i - 30)
                            search_end = min(len(lines), i + 30)
                            
                            for j in range(search_start, search_end):
                                check_line = lines[j].strip()
                                
                                # Look for year patterns with GPMP
                                year_gpmp_patterns = [
                                    r'(\d+\.\d{2})\s*(202[1-5])',  # GPMP followed by year
                                    r'(202[1-5])\s*(\d+\.\d{2})',  # Year followed by GPMP
                                ]
                                
                                for pattern in year_gpmp_patterns:
                                    matches = re.findall(pattern, check_line)
                                    for match in matches:
                                        if pattern == year_gpmp_patterns[0]:
                                            gpmp, year = float(match[0]), int(match[1])
                                        else:
                                            year, gpmp = int(match[0]), float(match[1])
                                        
                                        # Look for grade distribution data near this
                                        # Check lines around for grade numbers
                                        for k in range(max(search_start, j - 5), min(search_end, j + 5)):
                                            data_line = lines[k].strip()
                                            
                                            # Look for patterns with multiple numbers (grade distribution)
                                            numbers = re.findall(r'\d+', data_line)
                                            
                                            # We expect at least 10 numbers for grades A+ to G
                                            if len(numbers) >= 10:
                                                # This looks like grade distribution data
                                                print(f"  Year {year}: Found grade data with {len(numbers)} numbers: {numbers[:10]}")
                                                
                                                grades = {
                                                    'A+': int(numbers[0]) if len(numbers) > 0 else 0,
                                                    'A': int(numbers[1]) if len(numbers) > 1 else 0,
                                                    'A-': int(numbers[2]) if len(numbers) > 2 else 0,
                                                    'B+': int(numbers[3]) if len(numbers) > 3 else 0,
                                                    'B': int(numbers[4]) if len(numbers) > 4 else 0,
                                                    'C+': int(numbers[5]) if len(numbers) > 5 else 0,
                                                    'C': int(numbers[6]) if len(numbers) > 6 else 0,
                                                    'D': int(numbers[7]) if len(numbers) > 7 else 0,
                                                    'E': int(numbers[8]) if len(numbers) > 8 else 0,
                                                    'G': int(numbers[9]) if len(numbers) > 9 else 0,
                                                }
                                                
                                                total = sum(grades.values())
                                                passed = sum(grades[g] for g in ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D'])
                                                pass_rate = (passed / total * 100) if total > 0 else 0
                                                
                                                subject_data[year] = {
                                                    'gpmp': gpmp,
                                                    'grades': grades,
                                                    'candidates': total,
                                                    'passed': passed,
                                                    'pass_rate': round(pass_rate, 2)
                                                }
                                                
                                                print(f"    Year {year}: GPMP={gpmp}, Total={total}, Grades={grades}")
                                                break
                            
                            # Store the collected data
                            if subject_data:
                                data['spm_historical']['subjects'][subject] = []
                                for year in [2021, 2022, 2023, 2024, 2025]:
                                    if year in subject_data:
                                        data['spm_historical']['subjects'][subject].append(subject_data[year])
                                    else:
                                        data['spm_historical']['subjects'][subject].append({
                                            'gpmp': 0.0,
                                            'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0},
                                            'candidates': 0,
                                            'passed': 0,
                                            'pass_rate': 0.0
                                        })
                                
                                print(f"  Stored data for years: {list(subject_data.keys())}")
                            break
                    
                    i += 1
            
            # Extract overall school statistics
            print("\nExtracting overall school statistics...")
            
            # Look for overall patterns in the text
            lines = full_text.split('\n')
            for line in lines:
                # Look for patterns like: "2.42 88 100.00 88" (GPMP candidates pass_rate passed)
                overall_pattern = r'(\d+\.\d{2})\s+(\d+)\s+(\d+\.\d{2})\s+(\d+)'
                match = re.search(overall_pattern, line)
                
                if match:
                    gpmp = float(match.group(1))
                    candidates = int(match.group(2))
                    pass_rate = float(match.group(3))
                    passed = int(match.group(4))
                    
                    print(f"Found overall data: GPMP={gpmp}, Candidates={candidates}, Passed={passed}, Pass Rate={pass_rate}%")
                    
                    # Try to find the year for this data
                    # Look in nearby lines for year
                    line_idx = lines.index(line)
                    for j in range(max(0, line_idx - 5), min(len(lines), line_idx + 5)):
                        year_match = re.search(r'\b(202[1-5])\b', lines[j])
                        if year_match:
                            year = int(year_match.group(1))
                            data['spm_historical']['overall_stats'][year] = {
                                'gpmp': gpmp,
                                'candidates': candidates,
                                'passed': passed,
                                'pass_rate': pass_rate
                            }
                            print(f"  Assigned to year {year}")
                            break
            
            # Print summary
            print(f"\n=== EXTRACTION SUMMARY ===")
            print(f"Subjects extracted: {len(data['spm_historical']['subjects'])}")
            for subject, years_data in data['spm_historical']['subjects'].items():
                years_with_data = [i+2021 for i, year_data in enumerate(years_data) if year_data['candidates'] > 0]
                if years_with_data:
                    print(f"  {subject}: {years_with_data}")
            
            print(f"Overall stats years: {list(data['spm_historical']['overall_stats'].keys())}")
            
            return data
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_exact_data(data, filename='spm_historical_exact.json'):
    """Save the exact extracted SPM data"""
    if data:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Exact SPM data saved to {filename}")
    else:
        print("No data to save")

if __name__ == "__main__":
    data = extract_exact_spm_data("Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025.pdf")
    save_exact_data(data)
