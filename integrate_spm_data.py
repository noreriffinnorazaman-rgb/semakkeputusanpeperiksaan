import json

def integrate_spm_historical():
    """Integrate SPM historical data into main spm_data.json"""
    
    # Load main data
    with open('spm_data.json', 'r', encoding='utf-8') as f:
        main_data = json.load(f)
    
    # Load SPM historical data
    with open('spm_historical.json', 'r', encoding='utf-8') as f:
        spm_hist = json.load(f)
    
    # Add SPM historical data to main data
    main_data['spm_historical'] = spm_hist['spm_historical']
    
    # Save updated main data
    with open('spm_data.json', 'w', encoding='utf-8') as f:
        json.dump(main_data, f, indent=2, ensure_ascii=False)
    
    print("SPM historical data integrated into spm_data.json")
    print(f"Added {len(main_data['spm_historical']['subjects'])} subjects")
    print(f"Years: {main_data['spm_historical']['years']}")

if __name__ == "__main__":
    integrate_spm_historical()
