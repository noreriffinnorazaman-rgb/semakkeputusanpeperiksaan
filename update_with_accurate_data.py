import json

def update_system_with_accurate_data():
    """Update main system with accurate SPM data"""
    
    print("=" * 80)
    print("UPDATING DAPA SYSTEM WITH ACCURATE SPM DATA")
    print("=" * 80)
    
    # Load accurate SPM data
    with open('spm_historical_accurate.json', 'r', encoding='utf-8') as f:
        spm_data = json.load(f)
    print("✅ Loaded accurate SPM data")
    
    # Load main system data
    with open('spm_data.json', 'r', encoding='utf-8') as f:
        main_data = json.load(f)
    print("✅ Loaded main system data")
    
    # Update main data with SPM historical data
    main_data['spm_historical'] = spm_data['spm_historical']
    print("✅ Updated main data with SPM historical data")
    
    # Save updated main data
    with open('spm_data.json', 'w', encoding='utf-8') as f:
        json.dump(main_data, f, indent=2, ensure_ascii=False)
    print("✅ Saved updated spm_data.json")
    
    # Create backup
    with open('spm_data_backup.json', 'w', encoding='utf-8') as f:
        json.dump(main_data, f, indent=2, ensure_ascii=False)
    print("✅ Created backup: spm_data_backup.json")
    
    # Display summary
    print("\n" + "=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print(f"Subjects updated: {len(main_data['spm_historical']['subjects'])}")
    print(f"Years covered: {main_data['spm_historical']['years']}")
    
    # Show Sejarah data as requested
    print(f"\nSEJARAH SPM RESULTS:")
    sejarah_data = main_data['spm_historical']['subjects']['Sejarah']
    for i, year in enumerate([2021, 2022, 2023, 2024, 2025]):
        data = sejarah_data[i]
        print(f"  {year}: GPMP={data['gpmp']}, Candidates={data['candidates']}, Passed={data['passed']}, Pass Rate={data['pass_rate']}%")
        print(f"    Grades: A+={data['grades']['A+']}, A={data['grades']['A']}, A-={data['grades']['A-']}, B+={data['grades']['B+']}, B={data['grades']['B']}")
        print(f"           C+={data['grades']['C+']}, C={data['grades']['C']}, D={data['grades']['D']}, E={data['grades']['E']}, G={data['grades']['G']}")
    
    print("\n✅ System updated successfully!")
    print("=" * 80)
    
    return main_data

if __name__ == "__main__":
    data = update_system_with_accurate_data()
