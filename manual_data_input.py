"""
MANUAL SPM DATA INPUT
This script allows you to manually input the exact SPM data from your PDF
"""

import json

def input_spm_data_manually():
    """Input SPM data manually from PDF"""
    
    print("=" * 80)
    print("MANUAL SPM DATA INPUT FROM PDF")
    print("=" * 80)
    print("\nPlease have your PDF 'Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025' ready.")
    print("We will input the data subject by subject, year by year.")
    print("=" * 80)
    
    data = {
        'spm_historical': {
            'years': [2021, 2022, 2023, 2024, 2025],
            'subjects': {},
            'overall_stats': {}
        }
    }
    
    # Input overall statistics first
    print("\n=== OVERALL SCHOOL STATISTICS ===")
    for year in [2021, 2022, 2023, 2024, 2025]:
        print(f"\nYear {year}:")
        try:
            gpmp = float(input(f"  GPMP for {year}: "))
            candidates = int(input(f"  Number of candidates: "))
            passed = int(input(f"  Number passed: "))
            pass_rate = (passed / candidates * 100) if candidates > 0 else 0
            
            data['spm_historical']['overall_stats'][year] = {
                'gpmp': gpmp,
                'candidates': candidates,
                'passed': passed,
                'pass_rate': round(pass_rate, 2)
            }
        except ValueError:
            print(f"  Invalid input for {year}, using 0 values")
            data['spm_historical']['overall_stats'][year] = {
                'gpmp': 0.0, 'candidates': 0, 'passed': 0, 'pass_rate': 0.0
            }
    
    # Input subject data
    subjects = ['Bahasa Melayu', 'Bahasa Inggeris', 'Matematik', 'Sains', 
               'Sejarah', 'Geografi', 'Pendidikan Moral', 'Fizik', 'Kimia', 'Biologi']
    
    for subject in subjects:
        print(f"\n=== {subject.upper()} ===")
        subject_data = []
        
        for year in [2021, 2022, 2023, 2024, 2025]:
            print(f"\n{subject} - Year {year}:")
            try:
                gpmp = float(input(f"  GPMP: "))
                print("  Grade distribution (A+, A, A-, B+, B, C+, C, D, E, G):")
                a_plus = int(input("    A+: "))
                a = int(input("    A: "))
                a_minus = int(input("    A-: "))
                b_plus = int(input("    B+: "))
                b = int(input("    B: "))
                c_plus = int(input("    C+: "))
                c = int(input("    C: "))
                d = int(input("    D: "))
                e = int(input("    E: "))
                g = int(input("    G: "))
                
                grades = {
                    'A+': a_plus, 'A': a, 'A-': a_minus, 'B+': b_plus, 'B': b,
                    'C+': c_plus, 'C': c, 'D': d, 'E': e, 'G': g
                }
                
                total = sum(grades.values())
                passed = sum(grades[g] for g in ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D'])
                pass_rate = (passed / total * 100) if total > 0 else 0
                
                subject_data.append({
                    'gpmp': gpmp,
                    'grades': grades,
                    'candidates': total,
                    'passed': passed,
                    'pass_rate': round(pass_rate, 2)
                })
                
                print(f"  -> Total candidates: {total}, Passed: {passed}, Pass rate: {pass_rate:.1f}%")
                
            except ValueError:
                print(f"  Invalid input for {subject} {year}, using 0 values")
                subject_data.append({
                    'gpmp': 0.0,
                    'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0},
                    'candidates': 0,
                    'passed': 0,
                    'pass_rate': 0.0
                })
        
        data['spm_historical']['subjects'][subject] = subject_data
    
    return data

def save_manual_data(data, filename='spm_historical_manual.json'):
    """Save manually input SPM data"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nManual SPM data saved to {filename}")

if __name__ == "__main__":
    data = input_spm_data_manually()
    save_manual_data(data)
    
    print("\n" + "=" * 80)
    print("DATA INPUT COMPLETE!")
    print("=" * 80)
    print(f"Subjects entered: {len(data['spm_historical']['subjects'])}")
    print(f"Years: {data['spm_historical']['years']}")
    print("\nNext step: Update the main system with this data")
    print("=" * 80)
