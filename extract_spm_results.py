import PyPDF2
import re
import json
from collections import defaultdict

def extract_spm_results(pdf_path):
    """Extract SPM results from the 5-year analysis PDF"""
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
            text = ""
            
            # Extract text from all pages
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            print("Extracted PDF text, processing...")
            
            # Look for subject performance patterns
            # Common patterns in Malaysian school analysis PDFs
            subject_patterns = [
                r'([A-Z\s]+)\s+(\d{4})\s+(\d+)\s+(\d+)\s+(\d+\.\d+)%',  # Subject Year Candidates Pass %
                r'([A-Z\s]+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)%',  # Subject Candidates Pass %
                r'([A-Z\s]+)\s+(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)%',  # More detailed
            ]
            
            # Extract subject data
            subjects_data = defaultdict(lambda: defaultdict(dict))
            
            # Look for specific subjects
            subjects_to_find = [
                'BAHASA MELAYU', 'BAHASA INGGERIS', 'MATEMATIK', 
                'SAINS', 'SEJARAH', 'PENDIDIKAN MORAL',
                'FIZIK', 'KIMIA', 'BIOLOGI', 'MATEMATIK TAMBAHAN'
            ]
            
            lines = text.split('\n')
            current_year = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect year headers
                year_match = re.search(r'(\d{4})', line)
                if year_match:
                    year = int(year_match.group(1))
                    if 2021 <= year <= 2025:
                        current_year = year
                        continue
                
                # Look for subject data
                for subject in subjects_to_find:
                    if subject in line.upper():
                        # Extract numbers from the line
                        numbers = re.findall(r'\d+', line)
                        percentages = re.findall(r'\d+\.\d+', line)
                        
                        if len(numbers) >= 2 and current_year:
                            # Try to extract candidates and pass rate
                            candidates = numbers[-2] if len(numbers) >= 2 else numbers[0]
                            passed = numbers[-1] if len(numbers) >= 2 else numbers[1]
                            pass_rate = percentages[0] if percentages else "0.0"
                            
                            subjects_data[subject][current_year] = {
                                'candidates': int(candidates),
                                'passed': int(passed),
                                'pass_rate': float(pass_rate)
                            }
            
            # Convert to final format
            for subject, years_data in subjects_data.items():
                data['spm_historical']['subjects'][subject] = []
                for year in [2021, 2022, 2023, 2024, 2025]:
                    if year in years_data:
                        data['spm_historical']['subjects'][subject].append(years_data[year])
                    else:
                        data['spm_historical']['subjects'][subject].append({
                            'candidates': 0,
                            'passed': 0,
                            'pass_rate': 0.0
                        })
            
            # Extract overall school statistics
            overall_patterns = [
                r'KELULUSAN\s+MENGIKUT\s+TAHUN\s+(\d{4})\s+(\d+)\s+(\d+)\s+(\d+\.\d+)%',
                r'GPS\s+(\d{4})\s*:\s*(\d+\.\d+)',
                r'PURATA\s+MATA\s+PELAJARAN\s+(\d{4})\s*:\s*(\d+\.\d+)'
            ]
            
            for line in lines:
                for pattern in overall_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        groups = match.groups()
                        if len(groups) >= 2:
                            year = int(groups[0])
                            if 2021 <= year <= 2025:
                                if 'KELULUSAN' in pattern.upper():
                                    data['spm_historical']['overall_stats'][year] = {
                                        'candidates': int(groups[1]),
                                        'passed': int(groups[2]),
                                        'pass_rate': float(groups[3])
                                    }
                                elif 'GPS' in pattern.upper():
                                    if 'gps' not in data['spm_historical']['overall_stats'][year]:
                                        data['spm_historical']['overall_stats'][year]['gps'] = float(groups[1])
                                elif 'PURATA' in pattern.upper():
                                    if 'avg_subjects' not in data['spm_historical']['overall_stats'][year]:
                                        data['spm_historical']['overall_stats'][year]['avg_subjects'] = float(groups[1])
            
            print(f"Extracted data for {len(subjects_data)} subjects")
            print("Subjects found:", list(subjects_data.keys()))
            
            return data
            
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def save_spm_data(data, output_file='spm_historical.json'):
    """Save extracted SPM data to JSON file"""
    if data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"SPM data saved to {output_file}")
    else:
        print("No data to save")

if __name__ == "__main__":
    pdf_path = "Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025.pdf"
    spm_data = extract_spm_results(pdf_path)
    save_spm_data(spm_data)
