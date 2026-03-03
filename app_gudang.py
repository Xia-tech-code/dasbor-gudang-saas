import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="SaaS Dasbor Gudang", layout="wide")

# ==========================================
# 0. PERSIAPAN DATABASE & TABEL BUKU CATATAN (LOG)
# ==========================================
koneksi = sqlite3.connect('gudang_kita.db')
kurir = koneksi.cursor()

# Membuat tabel baru khusus untuk mencatat sejarah (Riwayat Transaksi)
kurir.execute('''
    CREATE TABLE IF NOT EXISTS Log_Transaksi (
        id_log INTEGER PRIMARY KEY AUTOINCREMENT,
        waktu TEXT,
        operator TEXT,
        nama_barang TEXT,
        jenis_transaksi TEXT,
        jumlah INTEGER,
        keterangan TEXT
    )
''')
koneksi.commit()
koneksi.close()

# ==========================================
# 1. SATPAM DIGITAL (LOGIN)
# ==========================================
st.title("🔒 Portal Akses Karyawan")
password_input = st.text_input("Masukkan Password Rahasia:", type="password")

if password_input != "bosgudang123":
    if password_input != "":
        st.error("❌ Akses Ditolak! Password salah.")
    st.stop()

st.success("✅ Akses Diterima! Memuat dasbor...")
st.markdown("---")

st.title("📦 Dasbor Manajemen Gudang (Versi Pro / Enterprise)")
st.markdown("---")

# ==========================================
# 2. AMBIL DATA DARI BRANKAS
# ==========================================
koneksi = sqlite3.connect('gudang_kita.db')
data_gudang = pd.read_sql_query("SELECT * FROM Master_Barang", koneksi)
koneksi.close()

# Waktu saat ini (Otomatis dari jam laptop/server)
waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==========================================
# 3. PANEL KIRI: FITUR BARANG MASUK & KELUAR DENGAN LOG
# ==========================================
st.sidebar.header("➕ Tambah Barang Baru")
with st.sidebar.form("form_tambah_barang", clear_on_submit=True):
    input_nama = st.text_input("Nama Barang")
    input_beli = st.number_input("Harga Beli (Rp)", min_value=0, step=1000)
    input_jual = st.number_input("Harga Jual (Rp)", min_value=0, step=1000)
    input_stok = st.number_input("Jumlah Stok Awal", min_value=0, step=1)
    
    # FITUR BARU: Siapa yang input dan alasannya
    operator_masuk = st.text_input("Nama Karyawan (Admin)")
    keterangan_masuk = st.text_input("Keterangan (misal: Stok Awal Pabrik)")
    
    if st.form_submit_button("Simpan ke Database"):
        koneksi = sqlite3.connect('gudang_kita.db')
        kurir = koneksi.cursor()
        
        # 1. Masukkan ke Master Barang
        kurir.execute('''
            INSERT INTO Master_Barang (nama_barang, harga_beli, harga_jual, stok)
            VALUES (?, ?, ?, ?)
        ''', (input_nama, input_beli, input_jual, input_stok))
        
        # 2. Masukkan ke Buku Catatan Sejarah (Log Transaksi)
        kurir.execute('''
            INSERT INTO Log_Transaksi (waktu, operator, nama_barang, jenis_transaksi, jumlah, keterangan)
            VALUES (?, ?, ?, 'MASUK', ?, ?)
        ''', (waktu_sekarang, operator_masuk, input_nama, input_stok, keterangan_masuk))
        
        koneksi.commit()
        koneksi.close()
        st.sidebar.success("Barang berhasil ditambahkan!")
        st.rerun()

st.sidebar.markdown("---")

st.sidebar.header("➖ Barang Keluar (Kasir)")
daftar_nama_barang = data_gudang['nama_barang'].tolist() if not data_gudang.empty else []

with st.sidebar.form("form_barang_keluar", clear_on_submit=True):
    barang_dipilih = st.selectbox("Pilih Barang", daftar_nama_barang)
    jumlah_keluar = st.number_input("Jumlah Keluar", min_value=1, step=1)
    
    # FITUR BARU: Siapa yang input dan alasannya
    operator_keluar = st.text_input("Nama Karyawan (Admin)")
    keterangan_keluar = st.text_input("Keterangan (misal: Terjual, Rusak, Proyek A)")
    
    if st.form_submit_button("Kurangi Stok"):
        stok_saat_ini = data_gudang.loc[data_gudang['nama_barang'] == barang_dipilih, 'stok'].values[0]
        
        if jumlah_keluar > stok_saat_ini:
            st.sidebar.error(f"GAGAL! Stok {barang_dipilih} sisa {stok_saat_ini}.")
        else:
            koneksi = sqlite3.connect('gudang_kita.db')
            kurir = koneksi.cursor()
            
            # 1. Update/Kurangi stok di Master Barang
            kurir.execute('''
                UPDATE Master_Barang 
                SET stok = stok - ? 
                WHERE nama_barang = ?
            ''', (jumlah_keluar, barang_dipilih))
            
            # 2. Catat ke Buku Sejarah (Log Transaksi)
            kurir.execute('''
                INSERT INTO Log_Transaksi (waktu, operator, nama_barang, jenis_transaksi, jumlah, keterangan)
                VALUES (?, ?, ?, 'KELUAR', ?, ?)
            ''', (waktu_sekarang, operator_keluar, barang_dipilih, jumlah_keluar, keterangan_keluar))
            
            koneksi.commit()
            koneksi.close()
            st.sidebar.success(f"Berhasil mengeluarkan {jumlah_keluar} {barang_dipilih}!")
            st.rerun()

# ==========================================
# 4. TAMPILAN DASHBOARD UTAMA
# ==========================================
koneksi = sqlite3.connect('gudang_kita.db')
data_gudang_terbaru = pd.read_sql_query("SELECT * FROM Master_Barang", koneksi)

# Menarik data sejarah dari buku catatan, diurutkan dari yang paling baru (DESC)
data_log_transaksi = pd.read_sql_query("SELECT waktu, operator, nama_barang, jenis_transaksi, jumlah, keterangan FROM Log_Transaksi ORDER BY id_log DESC", koneksi)
koneksi.close()

data_gudang_terbaru['Total_Nilai_Aset'] = data_gudang_terbaru['harga_beli'] * data_gudang_terbaru['stok']
total_aset_rupiah = data_gudang_terbaru['Total_Nilai_Aset'].sum()

st.subheader("Ringkasan Keuangan")
st.metric(label="Total Nilai Aset Gudang", value=f"Rp {total_aset_rupiah:,.0f}")
st.write("")

kolom_kiri, kolom_kanan = st.columns(2)
with kolom_kiri:
    st.subheader("📋 Stok Tersedia")
    st.dataframe(data_gudang_terbaru[['nama_barang', 'harga_beli', 'stok', 'Total_Nilai_Aset']], use_container_width=True)
with kolom_kanan:
    st.subheader("📊 Visualisasi Stok")
    st.bar_chart(data_gudang_terbaru.set_index('nama_barang')['stok'])

# ==========================================
# FITUR BARU: TABEL RIWAYAT TRANSAKSI LENGKAP
# ==========================================
st.markdown("---")
st.subheader("🕵️‍♂️ CCTV Gudang: Riwayat Transaksi (Audit Trail)")

# Menampilkan tabel riwayat jika datanya sudah ada
if not data_log_transaksi.empty:
    st.dataframe(data_log_transaksi, use_container_width=True)
else:
    st.info("Belum ada pergerakan barang yang tercatat.")

# Fitur Cetak
st.markdown("---")
st.subheader("🖨️ Cetak Laporan (Excel/CSV)")
data_csv = data_gudang_terbaru.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Stok Saat Ini", data=data_csv, file_name="Stok_Gudang.csv", mime="text/csv")

# Download untuk Riwayat Transaksi
log_csv = data_log_transaksi.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Riwayat Transaksi Lengkap", data=log_csv, file_name="Riwayat_Gudang.csv", mime="text/csv")
