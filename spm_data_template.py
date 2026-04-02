"""
SPM HISTORICAL DATA TEMPLATE
Please fill in the exact figures from your PDF "Analisis Pencapaian MP Sekolah 5 Tahun SPM 2021-2025"

Instructions:
1. Look at each subject page in the PDF
2. Find the grade distribution for each year (2021-2025)
3. Input the exact numbers for A+, A, A-, B+, B, C+, C, D, E, G
4. Also input the GPMP values shown in the PDF
5. Run this script to generate the accurate data file
"""

import json

def create_spm_data_from_pdf():
    """Create SPM data from exact PDF figures - PLEASE UPDATE WITH YOUR PDF DATA"""
    
    data = {
        'spm_historical': {
            'years': [2021, 2022, 2023, 2024, 2025],
            'subjects': {},
            'overall_stats': {}
        }
    }
    
    # =================================================================
    # PLEASE UPDATE THESE VALUES WITH EXACT FIGURES FROM YOUR PDF
    # =================================================================
    
    # Overall school statistics (from PDF headers)
    # Look for lines like: "2.42 88 100.00 88" (GPMP candidates pass_rate passed)
    data['spm_historical']['overall_stats'] = {
        2021: {'gpmp': 0.0, 'candidates': 0, 'passed': 0, 'pass_rate': 0.0},  # UPDATE FROM PDF
        2022: {'gpmp': 0.0, 'candidates': 0, 'passed': 0, 'pass_rate': 0.0},  # UPDATE FROM PDF
        2023: {'gpmp': 0.0, 'candidates': 0, 'passed': 0, 'pass_rate': 0.0},  # UPDATE FROM PDF
        2024: {'gpmp': 0.0, 'candidates': 0, 'passed': 0, 'pass_rate': 0.0},  # UPDATE FROM PDF
        2025: {'gpmp': 0.0, 'candidates': 0, 'passed': 0, 'pass_rate': 0.0}   # UPDATE FROM PDF
    }
    
    # Subject-wise data - UPDATE WITH EXACT PDF FIGURES
    subjects_template = {
        'Bahasa Melayu': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Bahasa Inggeris': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Matematik': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Sains': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Sejarah': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Geografi': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Fizik': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Kimia': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Biologi': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        },
        'Pendidikan Moral': {
            2021: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2022: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2023: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2024: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}},
            2025: {'gpmp': 0.0, 'grades': {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'G': 0}}
        }
    }
    
    # Calculate candidates, passed, and pass_rate for each subject/year
    for subject, years_data in subjects_template.items():
        data['spm_historical']['subjects'][subject] = []
        for year in [2021, 2022, 2023, 2024, 2025]:
            year_data = years_data[year]
            grades = year_data['grades']
            total = sum(grades.values())
            passed = sum(grades[g] for g in ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D'])
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            data['spm_historical']['subjects'][subject].append({
                'gpmp': year_data['gpmp'],
                'grades': grades,
                'candidates': total,
                'passed': passed,
                'pass_rate': round(pass_rate, 2)
            })
    
    return data

def save_template_data(data, filename='spm_historical_from_pdf.json'):
    """Save the PDF-based SPM data"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"SPM data from PDF saved to {filename}")
    print("\nPLEASE UPDATE THE TEMPLATE WITH YOUR EXACT PDF FIGURES BEFORE USING!")

if __name__ == "__main__":
    print("=" * 80)
    print("SPM HISTORICAL DATA TEMPLATE")
    print("=" * 80)
    print("\nPlease edit this file and update the template with exact figures from your PDF.")
    print("Look for:")
    print("1. GPMP values for each subject/year")
    print("2. Grade distributions (A+, A, A-, B+, B, C+, C, D, E, G)")
    print("3. Overall statistics (candidates, passed, pass rates)")
    print("\nAfter updating, run this script again to generate the data file.")
    print("=" * 80)
    
    data = create_spm_data_from_pdf()
    save_template_data(data)
