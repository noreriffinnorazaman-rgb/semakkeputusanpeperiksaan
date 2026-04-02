import PyPDF2
import re
import json
from collections import defaultdict

def extract_spm_advanced(pdf_path):
    """Advanced extraction of SPM results from the PDF"""
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
            full_text = ""
            
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            print("Extracting SPM data from PDF...")
            
            # Parse the structured data
            lines = full_text.split('\n')
            current_subject = None
            subject_data = defaultdict(lambda: defaultdict(dict))
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Detect subject names (they appear at the end of data blocks)
                if any(subject in line for subject in ['Bahasa Melayu', 'Sejarah', 'Geografi', 'Matematik', 
                                                      'Sains', 'Fizik', 'Kimia', 'Biologi', 
                                                      'Bahasa Inggeris', 'Pendidikan Moral']):
                    
                    # Extract subject name
                    for subject in ['Bahasa Melayu', 'Sejarah', 'Geografi', 'Matematik', 
                                   'Sains', 'Fizik', 'Kimia', 'Biologi', 
                                   'Bahasa Inggeris', 'Pendidikan Moral']:
                        if subject in line:
                            current_subject = subject
                            break
                    
                    # Look backwards for the data associated with this subject
                    # The data should be in the lines before the subject name
                    j = i - 1
                    year_data = {}
                    
                    while j >= 0 and j >= i - 20:  # Look back up to 20 lines
                        prev_line = lines[j].strip()
                        
                        # Look for year patterns and GPMP
                        year_match = re.search(r'\b(202[1-5])\b', prev_line)
                        gpmp_match = re.search(r'\b(\d+\.\d{2})\s*202[1-5]\b', prev_line)
                        
                        if year_match and gpmp_match:
                            year = int(year_match.group(1))
                            gpmp = float(gpmp_match.group(1))
                            
                            # Look for the actual data line (usually 2-3 lines before year)
                            data_line_idx = j - 2
                            if data_line_idx >= 0:
                                data_line = lines[data_line_idx].strip()
                                numbers = re.findall(r'\d+', data_line)
                                
                                if len(numbers) >= 10:  # Should have at least 10 numbers for grades
                                    # Parse grade distribution
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
                                    
                                    # Calculate totals
                                    total_candidates = sum(grades.values())
                                    total_passed = sum(grades[g] for g in ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D'])
                                    pass_rate = (total_passed / total_candidates * 100) if total_candidates > 0 else 0
                                    
                                    year_data[year] = {
                                        'gpmp': gpmp,
                                        'grades': grades,
                                        'candidates': total_candidates,
                                        'passed': total_passed,
                                        'pass_rate': round(pass_rate, 2)
                                    }
                                    break
                        j -= 1
                    
                    # Store the collected data
                    if year_data and current_subject:
                        subject_data[current_subject] = year_data
                        print(f"Extracted data for {current_subject}: {list(year_data.keys())}")
                
                i += 1
            
            # Convert to final format
            for subject, years_data in subject_data.items():
                data['spm_historical']['subjects'][subject] = []
                for year in [2021, 2022, 2023, 2024, 2025]:
                    if year in years_data:
                        data['spm_historical']['subjects'][subject].append(years_data[year])
                    else:
                        data['spm_historical']['subjects'][subject].append({
                            'gpmp': 0.0,
                            'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0},
                            'candidates': 0,
                            'passed': 0,
                            'pass_rate': 0.0
                        })
            
            # Extract overall school GPMP trends
            overall_gpmp = {}
            lines = full_text.split('\n')
            
            for line in lines:
                # Look for overall GPMP patterns (usually at top of pages)
                gpmp_match = re.search(r'(\d+\.\d{2})\s+(\d+)\s+(\d+)\s+100\.00\s+(\d+)', line)
                if gpmp_match:
                    # This might be overall data, need to identify year
                    # Look for year in nearby lines
                    for i in range(max(0, lines.index(line) - 5), min(len(lines), lines.index(line) + 5)):
                        year_match = re.search(r'\b(202[1-5])\b', lines[i])
                        if year_match:
                            year = int(year_match.group(1))
                            overall_gpmp[year] = {
                                'gpmp': float(gpmp_match.group(1)),
                                'candidates': int(gpmp_match.group(4)),
                                'passed': int(gpmp_match.group(2)),
                                'pass_rate': round((int(gpmp_match.group(2)) / int(gpmp_match.group(4)) * 100), 2) if int(gpmp_match.group(4)) > 0 else 0
                            }
                            break
            
            data['spm_historical']['overall_stats'] = overall_gpmp
            
            print(f"\nExtraction complete!")
            print(f"Subjects extracted: {len(subject_data)}")
            print(f"Years with overall data: {list(overall_gpmp.keys())}")
            
            return data
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_spm_data(data, output_file='spm_historical.json'):
    """Save extracted SPM data to JSON file"""
    if data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"SPM data saved to {output_file}")
        
        # Also create a summary
        summary = {
            'total_subjects': len(data['spm_historical']['subjects']),
            'subjects': list(data['spm_historical']['subjects'].keys()),
            'years_available': [year for year in data['spm_historical']['years'] 
                              if any(data['spm_historical']['subjects'][s][year-2021]['candidates'] > 0 
                                   for s in data['spm_historical']['subjects'])]
        }
        
        with open('spm_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Summary saved to spm_summary.json")
    else:
        print("No data to save")

if __name__ == "__main__":
    spm_data = extract_spm_advanced("Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025.pdf")
    save_spm_data(spm_data)
