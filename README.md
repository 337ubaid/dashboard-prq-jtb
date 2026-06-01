# 📊 PRQ Dashboard - Witel Jatim Timur Bali (JTB)

Selamat datang di **PRQ Dashboard**, sebuah aplikasi analisis data interaktif berbasis web yang dibangun menggunakan **Streamlit** (Python). Aplikasi ini dirancang secara khusus untuk kebutuhan pemantauan, visualisasi, dan pelaporan performa pendapatan (revenue) segmen POTS/CBASE SME serta evaluasi performa scorecard wilayah melalui sistem **Impactful Telda** di lingkungan Witel Jatim Timur Bali (JTB).

---

## 🚀 Fitur Utama Dashboard

PRQ Dashboard dibagi menjadi dua modul halaman analisis utama yang kaya fitur dan interaktif:

### 1. 🔍 CBASE SME Dashboard (`pages/2_🔍_CBASE_SME.py`)
Modul ini berfokus pada visualisasi detail dan komparasi performa pendapatan (revenue) CBASE di segmen SME secara langsung dari database **BigQuery**.

*   **Integrasi BigQuery Real-Time**: Penarikan data performa pendapatan secara langsung dan dinamis menggunakan query agregasi & pivot di sisi BigQuery.
*   **Filter Data Multi-Dimensi**: Filter sidebar yang fleksibel memudahkan pengguna menyaring data berdasarkan:
    *   Tahun (Year ID)
    *   FLAG Revenue (scaling bulanan)
    *   Subsegmen Head Office (HO)
    *   Nama Account Manager (AM)
    *   Wilayah Telkom Daerah (Telda)
    *   Sentral Telepon Otomat (STO)
    *   Pencarian spesifik berdasarkan Nomor NIPNAS.
*   **Modern Glassmorphic KPI Cards**: Blok KPI premium yang menampilkan ringkasan performa berjalan (*Year-to-Date*):
    *   **Actual Revenue**: Nilai total pendapatan riil saat ini.
    *   **Target Revenue**: Target pendapatan yang ditentukan berdasarkan periode terpilih.
    *   **Overall Achievement**: Persentase pencapaian total dengan visualisasi *progress bar* interaktif yang berubah warna secara otomatis (Emerald Green ≥ 100%, Amber Orange ≥ 90%, Rose Red < 90%).
*   **Grafik Trend ECharts**: Line chart dinamis menggunakan Apache ECharts untuk menganalisis pergerakan tren *Actual Revenue vs Target Revenue* dari bulan ke bulan.
*   **Tabel Revenue Terkondisi**: Menyajikan data detail yang teragregasi lengkap dengan pewarnaan visual otomatis pada baris **Total** dan baris **Achievement**.
*   **Analisis Revenue Per Layanan**: Tab khusus untuk memantau performa pendapatan per kategori produk/layanan (misal: HSI, ASTINet, VPN, Call Center, Metro E, Cloud, POTs, dll.) berdasarkan pemetaan kode `GROUP5`.
*   **Rank Pelanggan**: Tab pemeringkat instan yang menyajikan **Top 10** dan **Bottom 10** pelanggan (NIPNAS) berdasarkan kontribusi total revenue mereka.
*   **Tautan SharePoint**: Akses cepat ke data eksternal untuk verifikasi nama pelanggan.

---

### 2. 🏆 Impactful Telda Scorecard Dashboard (`pages/3_🏆_Impactful_Telda.py`)
Modul penilaian terpusat yang menormalisasi dan mengevaluasi kinerja operasional 8 Telda di bawah Witel JTB menggunakan sistem kartu penilaian (*Scorecard*).

*   **14 Indikator Kinerja Terbobot (Weight 100%)**: Perhitungan performa dihitung berdasarkan metrik operasional berikut:
    *   *Revenue SME - POTS* (Bobot: 35%)
    *   *Revenue SME - NON POTS* (Bobot: 5%)
    *   *Revenue GOV* (Bobot: 5%)
    *   *Revenue PS* (Bobot: 5%)
    *   *Revenue SOE* (Bobot: 5%)
    *   *C3MR* (Bobot: 5% - Target standard: 98%)
    *   *HSI + WMS* (Bobot: 20%)
    *   *Bandwidth (BW)* (Bobot: 5%)
    *   *OCA* (Bobot: 2%)
    *   *Netmonk* (Bobot: 3%)
    *   *Eazy* (Bobot: 3%)
    *   *Pijar Sekolah* (Bobot: 2%)
    *   *LTS* (Bobot: 3% - Target standard: 56%)
    *   *Visit & Profiling* (Bobot: 2%)
*   **Glassmorphic Executive Bento Cards**: Widget ringkasan dinamis di bagian atas halaman yang menyajikan:
    *   Wilayah Telda dan Periode bulan terpilih.
    *   Total Skor Scorecard akumulatif.
    *   Perbandingan performa Telda terpilih terhadap Rata-rata Regional (menampilkan selisih poin lengkap dengan indikator arah ▲ atau ▼).
*   **Analisis Multi-Periode Komprehensif**:
    *   **📅 Quarter-to-Date (QTD)**: Akumulasi pencapaian target, realisasi, persentase keaktifan (*Achievement*), dan bobot nilai per kuartal (Q1 - Q4) untuk Telda terpilih.
    *   **📊 Month-to-Date (MTD)**: Perbandingan lengkap antar 8 Telda (Batu, Blitar, Bojonegoro, Kediri, Madiun, Malang, Nganjuk, Ponorogo) pada bulan terpilih untuk Target, Realisasi, Achievement (%), dan Poin/Skor.
    *   **📈 Year-to-Date (YTD)**: Performa kumulatif gabungan dari awal tahun hingga bulan berjalan untuk seluruh wilayah Telda.
*   **Performance Storytelling & Trend Chart**: Visualisasi line chart interaktif memetakan historis *Total Points* bulanan Telda terpilih berbanding lurus dengan garis rata-rata poin seluruh Telda se-Witel JTB.
*   **Actionable Insights Cerdas**: Rekomendasi otomatis berbasis data yang mengelompokkan:
    *   **Star Performers**: Indikator dengan kinerja luar biasa (mencapai target ≥ 100%).
    *   **Critical Focus Areas**: Indikator prioritas yang memerlukan evaluasi khusus karena berada di bawah standar target (< 90%).
*   **Audit Trail & Unduh CSV**: Kemampuan mengekspor seluruh tabel analisis (Target, Realisasi, Achievement, Score) ke dalam file CSV sekali klik, serta tab visualisasi baris data mentah terfilter.

---

## 📂 Struktur Direktori Proyek

```text
dashboard-prq-jtb/
│
├── app.py                      # Entry point / Halaman Utama Selamat Datang
├── requirements.txt            # Daftar pustaka & dependensi Python
├── data_rev_2025.csv           # File data pendukung internal
├── requirements.txt            # Daftar dependensi Python
│
├── pages/                      # Modul halaman Streamlit
│   ├── 2_🔍_CBASE_SME.py       # Halaman Dashboard CBASE SME (BigQuery)
│   └── 3_🏆_Impactful_Telda.py  # Halaman Dashboard Scorecard Impactful Telda (GSheet/CSV)
│
├── data/                       # Lapisan Ingesti & Konfigurasi Data
│   ├── __init__.py
│   ├── bq_client.py            # BigQuery Client & fungsi penarikan data bercache
│   ├── processing.py           # Pemetaan layanan & data target RKAP 2025-2026
│   └── sheet_raw.json          # File cadangan (fallback) offline Google Sheet
│
├── components/                 # Modul visualisasi reusable
│   ├── __init__.py
│   ├── charts.py               # Penyusunan grafik pendukung
│   └── metrics.py              # Template kartu metrik mini
│
├── utils/                      # Fungsi helper & utilitas logika bisnis
│   ├── __init__.py
│   ├── data_processing.py      # Sanitasi input angka & normalisasi struktur data GSheet
│   └── helpers.py              # Utilitas visual, format angka pendek (Tr, M, Jt), & styling tabel
│
└── .streamlit/
    └── secrets.toml            # [SENSITIF] Token kredensial GCP, BQ, dan Spreadsheet URL
```

---

## 🛠️ Panduan Instalasi & Menjalankan Lokal

### 1. Prasyarat (Prerequisites)
Pastikan komputer Anda sudah terinstal:
*   Python 3.10 atau versi di atasnya.
*   Akses internet (untuk mengunduh data BigQuery & Google Sheets).

### 2. Kloning & Pembuatan Virtual Environment
Buka terminal/command prompt di direktori proyek Anda:

```bash
# Buat Virtual Environment baru
python -m venv .venv

# Aktifkan Virtual Environment
# Di Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Di Windows (CMD):
.venv\Scripts\activate.bat
# Di macOS/Linux:
source .venv/bin/activate

# Pasang semua dependensi
pip install -r requirements.txt
```

### 3. Konfigurasi Kredensial (`secrets.toml`)
Aplikasi ini memerlukan akses BigQuery dan Google Sheets API. Buat sebuah file bernama `secrets.toml` di dalam folder `.streamlit` pada direktori utama proyek:

```toml
# .streamlit/secrets.toml

[bigquery]
dataset = "nama_dataset_bigquery_anda"

[sharepoint]
cek_nama_pelanggan = "https://link-sharepoint-anda/..."

[spreadsheet]
kpi_telda = "https://docs.google.com/spreadsheets/d/ID_SPREADSHEET_ANDA/edit"

# Kredensial Service Account GCP (Google Cloud Platform)
[gcp_service_account]
type = "service_account"
project_id = "project-gcp-anda"
private_key_id = "xxxxxxxxxxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\nMIICXAIBAAKBgQ...\n-----END PRIVATE KEY-----\n"
client_email = "service-account-anda@project-gcp-anda.iam.gserviceaccount.com"
client_id = "1234567890"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

> [!IMPORTANT]
> Pastikan email `client_email` dari Service Account di atas sudah diberikan akses berbagi (**Editor/Viewer**) ke Spreadsheet Google Sheet yang digunakan agar data scorecard dapat ditarik dengan lancar.

### 4. Menjalankan Aplikasi
Setelah virtual environment aktif dan secrets terkonfigurasi, jalankan perintah berikut:

```bash
streamlit run app.py
```
Aplikasi secara otomatis akan terbuka di browser Anda pada alamat default: `http://localhost:8501`.

---

## 🛡️ Keamanan & Ketahanan Sistem (Robustness)

Aplikasi ini dilengkapi dengan fitur pertahanan sistem untuk memastikan kestabilan performa:
1.  **Sistem Pembersih Angka Cerdas (`clean_numeric_val`)**: Fungsi penormalisasi data yang secara otomatis membersihkan simbol mata uang (`Rp`), spasi kosong, persentase (`%`), serta secara cerdas mendeteksi dan mengonversi format ribuan & desimal baik bergaya **Indonesia (titik sebagai ribuan, koma sebagai desimal)** maupun **Amerika/Inggris (koma sebagai ribuan, titik sebagai desimal)**.
2.  **Mekanisme Fallback Offline**: Apabila Google Sheets tidak dapat dijangkau karena kendala jaringan atau masalah kredensial API, sistem secara otomatis akan memuat data lokal melalui file cadangan JSON (`data/sheet_raw.json`) atau CSV lokal (`lokeer impactfull.csv`) sehingga dashboard tetap dapat diakses tanpa *crash*.
3.  **Caching Optimal**: Pemanfaatan decorator `@st.cache_data` dan `@st.cache_resource` dari Streamlit untuk menghemat biaya pemanggilan kueri BigQuery dan mengoptimalkan kecepatan respons dashboard saat filter diubah-ubah.

---

*Dikembangkan untuk Witel Jatim Timur Bali (JTB).*