import pandas as pd
import json
import os

def extract_all_data(excel_file):
    """Extract all data from the Excel file"""
    print(f"Loading Excel file: {excel_file}")
    xl = pd.ExcelFile(excel_file)
    
    all_data = {}
    
    # Extract basic information
    print("\n=== EXTRACTING BASIC INFORMATION ===")
    df_info = pd.read_excel(xl, sheet_name='MAKLUMAT ASAS', header=None)
    all_data['school_info'] = {
        'school_name': 'SMK TUANKU LAILATUL SHAHREEN',
        'school_code': 'REA0084',
        'principal': 'LILI MARIAM BINTI MOHAMMAD @ MOKHTAR',
        'grade': 'B',
        'exam_year': 2026,
        'form': 'LIMA'
    }
    
    # Extract student data from I sheets (Individual students)
    print("\n=== EXTRACTING STUDENT DATA ===")
    students = []
    i_sheets = [s for s in xl.sheet_names if s.startswith('I') and s[1:].isdigit()]
    
    for sheet in i_sheets:
        try:
            df = pd.read_excel(xl, sheet_name=sheet, header=None)
            student_data = {
                'sheet': sheet,
                'name': str(df.iloc[0, 1]) if pd.notna(df.iloc[0, 1]) else '',
                'class': str(df.iloc[1, 1]) if pd.notna(df.iloc[1, 1]) else '',
                'ic': str(df.iloc[2, 1]) if pd.notna(df.iloc[2, 1]) else '',
                'gender': str(df.iloc[3, 1]) if pd.notna(df.iloc[3, 1]) else '',
                'subjects': []
            }
            
            # Extract subject results (rows 11-22 typically contain subjects)
            for row_idx in range(11, min(23, len(df))):
                if pd.notna(df.iloc[row_idx, 1]):
                    subject_name = str(df.iloc[row_idx, 1])
                    if subject_name and subject_name not in ['JUMLAH GRED', 'JUMLAH MATA', 'JUMLAH M.PELAJARAN', 'GRED PURATA MURID']:
                        subject = {
                            'name': subject_name,
                            'tov': str(df.iloc[row_idx, 3]) if pd.notna(df.iloc[row_idx, 3]) else '',
                            'u1': str(df.iloc[row_idx, 6]) if pd.notna(df.iloc[row_idx, 6]) else '',
                            'ppt': str(df.iloc[row_idx, 9]) if pd.notna(df.iloc[row_idx, 9]) else '',
                            'spmc': str(df.iloc[row_idx, 12]) if pd.notna(df.iloc[row_idx, 12]) else '',
                            'etr': str(df.iloc[row_idx, 15]) if pd.notna(df.iloc[row_idx, 15]) else ''
                        }
                        student_data['subjects'].append(subject)
            
            if student_data['name']:
                students.append(student_data)
                print(f"  Extracted: {student_data['name']} ({sheet})")
        except Exception as e:
            print(f"  Error processing {sheet}: {e}")
    
    all_data['students'] = students
    print(f"\nTotal students extracted: {len(students)}")
    
    # Extract subject category sheets
    print("\n=== EXTRACTING SUBJECT CATEGORIES ===")
    
    # B sheets - Bahasa subjects
    b_sheets = [s for s in xl.sheet_names if s.startswith('B') and len(s) <= 3 and s[1:].isdigit()]
    all_data['bahasa_subjects'] = extract_subject_category(xl, b_sheets, 'Bahasa')
    
    # S sheets - Sains subjects
    s_sheets = [s for s in xl.sheet_names if s.startswith('S') and len(s) <= 3 and s[1:].isdigit()]
    all_data['sains_subjects'] = extract_subject_category(xl, s_sheets, 'Sains')
    
    # K sheets - Kemanusiaan subjects
    k_sheets = [s for s in xl.sheet_names if s.startswith('K') and len(s) <= 3 and s[1:].isdigit()]
    all_data['kemanusiaan_subjects'] = extract_subject_category(xl, k_sheets, 'Kemanusiaan')
    
    # V sheets - Vokasional subjects
    v_sheets = [s for s in xl.sheet_names if s.startswith('V') and len(s) <= 3 and s[1:].isdigit()]
    all_data['vokasional_subjects'] = extract_subject_category(xl, v_sheets, 'Vokasional')
    
    # Extract headcount and analysis data
    print("\n=== EXTRACTING HEADCOUNT DATA ===")
    try:
        df_headcount = pd.read_excel(xl, sheet_name='HEADCOUNT', header=None)
        all_data['headcount'] = df_headcount.fillna('').values.tolist()
    except:
        all_data['headcount'] = []
    
    print("\n=== EXTRACTING ANALYSIS DATA ===")
    try:
        df_kpi = pd.read_excel(xl, sheet_name='ANALISIS - KPI', header=None)
        all_data['analysis_kpi'] = df_kpi.fillna('').values.tolist()
    except:
        all_data['analysis_kpi'] = []
    
    return all_data

def extract_subject_category(xl, sheets, category_name):
    """Extract data from subject category sheets"""
    subjects = []
    for sheet in sheets:
        try:
            df = pd.read_excel(xl, sheet_name=sheet, header=None)
            subject_info = {
                'sheet': sheet,
                'category': category_name,
                'subject_name': str(df.iloc[0, 1]) if pd.notna(df.iloc[0, 1]) else '',
                'data': df.fillna('').values.tolist()
            }
            subjects.append(subject_info)
            print(f"  {category_name}: {subject_info['subject_name']} ({sheet})")
        except Exception as e:
            print(f"  Error processing {sheet}: {e}")
    return subjects

if __name__ == "__main__":
    excel_file = "REA0084 SMKTLS SPM 2026.xlsm (2).xlsx"
    
    if os.path.exists(excel_file):
        data = extract_all_data(excel_file)
        
        # Save to JSON
        output_file = "extracted_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== EXTRACTION COMPLETE ===")
        print(f"Data saved to: {output_file}")
        print(f"\nSummary:")
        print(f"  - Students: {len(data['students'])}")
        print(f"  - Bahasa subjects: {len(data['bahasa_subjects'])}")
        print(f"  - Sains subjects: {len(data['sains_subjects'])}")
        print(f"  - Kemanusiaan subjects: {len(data['kemanusiaan_subjects'])}")
        print(f"  - Vokasional subjects: {len(data['vokasional_subjects'])}")
    else:
        print(f"Error: File '{excel_file}' not found!")
