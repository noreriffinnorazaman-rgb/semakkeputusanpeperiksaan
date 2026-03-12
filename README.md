# SISTEM PENGURUSAN PEPERIKSAAN SPM 2026

Sistem pengurusan peperiksaan SPM yang canggih dan moden untuk **SMK TUANKU LAILATUL SHAHREEN (REA0084)**.

## ✨ Ciri-ciri Utama

### 📊 Pengurusan Data Lengkap
- **Ekstrak semua data** dari Excel (127 sheets)
- **54 Mata Pelajaran** merentas 4 kategori:
  - 8 Bahasa (Melayu, Inggeris, Cina, Tamil, Arab, dll)
  - 8 Sains (Fizik, Kimia, Biologi, Matematik, dll)
  - 14 Kemanusiaan (Sejarah, Geografi, Pendidikan Islam, dll)
  - 24 Vokasional (Pertanian, Perdagangan, Teknologi, dll)

### 👥 Pengurusan Pelajar
- Senarai lengkap pelajar dengan maklumat peribadi
- Keputusan peperiksaan (TOV, U1, PPT, SPMC, ETR)
- Tambah pelajar baru dengan borang interaktif
- Edit dan kemaskini maklumat pelajar
- Paparan terperinci setiap pelajar

### 📑 Laporan & Cetakan
- **Cetak laporan individu pelajar** (PDF)
- **Cetak ringkasan keseluruhan** (PDF)
- Format profesional dengan statistik lengkap
- Siap untuk dicetak dan diserahkan

### 🎨 Antara Muka Moden
- Reka bentuk responsif (Desktop, Tablet, Mobile)
- TailwindCSS untuk UI yang cantik
- Dashboard interaktif dengan statistik real-time
- Navigasi mudah dan intuitif

## 🚀 Cara Menggunakan

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Ekstrak Data dari Excel
```bash
python complete_extraction.py
```
Ini akan mengekstrak semua data dari `REA0084 SMKTLS SPM 2026.xlsm (2).xlsx` dan menyimpan ke `spm_data.json`.

### 3. Jalankan Aplikasi Web
```bash
python app.py
```

### 4. Buka Browser
Pergi ke: **http://localhost:5000**

## 📁 Struktur Sistem

```
DAPA SYSTEM NEW/
├── app.py                          # Aplikasi Flask utama
├── complete_extraction.py          # Script ekstrak data Excel
├── spm_data.json                   # Data JSON (auto-generated)
├── requirements.txt                # Python dependencies
├── templates/                      # HTML templates
│   ├── base.html                  # Template asas
│   ├── index.html                 # Dashboard
│   ├── students.html              # Senarai pelajar
│   ├── student_detail.html        # Butiran pelajar
│   ├── add_student.html           # Tambah pelajar
│   ├── edit_student.html          # Edit pelajar
│   ├── subjects.html              # Senarai subjek
│   └── subject_detail.html        # Butiran subjek
└── static/                         # Assets (CSS, JS, images)
```

## 📋 Menu Utama

1. **Dashboard** - Statistik keseluruhan dan maklumat sekolah
2. **Senarai Pelajar** - Lihat semua pelajar dan keputusan
3. **Mata Pelajaran** - Semua subjek mengikut kategori
4. **Tambah Pelajar** - Daftar pelajar baru dengan keputusan
5. **Cetak Ringkasan** - Laporan PDF keseluruhan

## 🎯 Fungsi Utama

### Untuk Pelajar
- ✅ Lihat maklumat lengkap
- ✅ Lihat keputusan semua subjek (TOV, U1, PPT, SPMC, ETR)
- ✅ Cetak laporan individu
- ✅ Edit dan kemaskini data

### Untuk Mata Pelajaran
- ✅ Lihat semua subjek mengikut kategori
- ✅ Statistik pencapaian setiap subjek
- ✅ Maklumat terperinci subjek

### Untuk Pentadbir
- ✅ Dashboard dengan statistik real-time
- ✅ Tambah pelajar baru
- ✅ Edit data pelajar
- ✅ Cetak laporan PDF
- ✅ Export dan import data

## 📊 Data Yang Diekstrak

### Dari Excel (127 Sheets):
- ✅ Maklumat Sekolah (MAKLUMAT ASAS)
- ✅ 50 Pelajar (I1-I50)
- ✅ 8 Subjek Bahasa (B1-B8)
- ✅ 8 Subjek Sains (S1-S8)
- ✅ 14 Subjek Kemanusiaan (K1-K14)
- ✅ 24 Subjek Vokasional (V1-V24)
- ✅ Headcount & Analisis
- ✅ Graf & Statistik

## 🖨️ Cetakan PDF

### Laporan Pelajar
- Maklumat pelajar lengkap
- Keputusan semua mata pelajaran
- Statistik (Jumlah Mata, Purata Gred)
- Format profesional

### Ringkasan Keseluruhan
- Maklumat sekolah
- Statistik semua kategori subjek
- Jumlah pelajar
- Format ringkas dan padat

## 💡 Tips Penggunaan

1. **Import Data Awal**: Jalankan `complete_extraction.py` untuk ekstrak data dari Excel
2. **Tambah Pelajar Baru**: Gunakan borang "Tambah Pelajar" untuk keputusan peperiksaan baru
3. **Edit Data**: Klik "Edit" pada mana-mana pelajar untuk kemaskini maklumat
4. **Cetak Laporan**: Gunakan butang "Cetak" untuk generate PDF
5. **Backup Data**: Simpan `spm_data.json` sebagai backup

## 🔧 Teknologi

- **Backend**: Flask (Python)
- **Frontend**: HTML5, TailwindCSS, JavaScript
- **Data**: JSON, Excel (openpyxl, pandas)
- **PDF**: ReportLab
- **UI Framework**: TailwindCSS

## 📞 Maklumat Sekolah

- **Nama**: SMK TUANKU LAILATUL SHAHREEN
- **Kod**: REA0084
- **Pengetua**: LILI MARIAM BINTI MOHAMMAD @ MOKHTAR
- **Gred**: B
- **Tahun**: 2026
- **Tingkatan**: LIMA

## 🎓 Sistem Gred SPM

- **A+**: 90-100 (Pekali: 0)
- **A**: 80-89 (Pekali: 1)
- **A-**: 70-79 (Pekali: 2)
- **B+**: 65-69 (Pekali: 3)
- **B**: 60-64 (Pekali: 4)
- **C+**: 55-59 (Pekali: 5)
- **C**: 50-54 (Pekali: 6)
- **D**: 45-49 (Pekali: 7)
- **E**: 40-44 (Pekali: 8)
- **G**: 1-39 (Pekali: 9)
- **TH**: 0 (Tidak Hadir)

---

**© 2026 SMK TUANKU LAILATUL SHAHREEN - Sistem Pengurusan SPM**
