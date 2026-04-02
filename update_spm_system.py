"""
UPDATE SPM SYSTEM WITH ACCURATE DATA
This script updates the main spm_data.json with accurate SPM historical data
"""

import json
import os

def update_spm_system():
    """Update the main DAPA system with accurate SPM data"""
    
    print("=" * 80)
    print("UPDATING DAPA SYSTEM WITH ACCURATE SPM DATA")
    print("=" * 80)
    
    # Check if manual data file exists
    manual_file = 'spm_historical_manual.json'
    if not os.path.exists(manual_file):
        print(f"❌ Error: {manual_file} not found!")
        print("Please run manual_data_input.py first to create the data file.")
        return False
    
    # Load the accurate SPM data
    try:
        with open(manual_file, 'r', encoding='utf-8') as f:
            spm_data = json.load(f)
        print(f"✅ Loaded SPM data from {manual_file}")
    except Exception as e:
        print(f"❌ Error loading {manual_file}: {e}")
        return False
    
    # Load the main system data
    try:
        with open('spm_data.json', 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        print("✅ Loaded main system data")
    except Exception as e:
        print(f"❌ Error loading spm_data.json: {e}")
        return False
    
    # Update the main data with SPM historical data
    main_data['spm_historical'] = spm_data['spm_historical']
    
    # Save the updated main data
    try:
        with open('spm_data.json', 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        print("✅ Updated spm_data.json with accurate SPM data")
    except Exception as e:
        print(f"❌ Error saving spm_data.json: {e}")
        return False
    
    # Create backup
    try:
        with open('spm_data_backup.json', 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        print("✅ Created backup: spm_data_backup.json")
    except Exception as e:
        print(f"⚠️ Warning: Could not create backup: {e}")
    
    # Display summary
    print("\n" + "=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print(f"Subjects updated: {len(main_data['spm_historical']['subjects'])}")
    print(f"Years covered: {main_data['spm_historical']['years']}")
    print(f"Overall stats years: {list(main_data['spm_historical']['overall_stats'].keys())}")
    
    # Show sample data
    print("\nSample data (Bahasa Melayu 2021):")
    if 'Bahasa Melayu' in main_data['spm_historical']['subjects']:
        bm_2021 = main_data['spm_historical']['subjects']['Bahasa Melayu'][0]
        print(f"  GPMP: {bm_2021['gpmp']}")
        print(f"  Candidates: {bm_2021['candidates']}")
        print(f"  Passed: {bm_2021['passed']}")
        print(f"  Pass Rate: {bm_2021['pass_rate']}%")
        print(f"  Grades: {bm_2021['grades']}")
    
    print("\n✅ System updated successfully!")
    print("Next steps:")
    print("1. Test the system locally: python app.py")
    print("2. Check /spm-historical page")
    print("3. Deploy to GitHub: git add . && git commit && git push")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = update_spm_system()
    if success:
        print("\n🎉 Ready to deploy accurate SPM data!")
    else:
        print("\n❌ Update failed. Please check the errors above.")
