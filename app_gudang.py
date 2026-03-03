import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="SaaS Dasbor Gudang", layout="wide")
import streamlit as st
import pandas as pd
import sqlite3

# 1. Konfigurasi awal halaman web
st.set_page_config(page_title="SaaS Dasbor Gudang", layout="wide")

# ==========================================
# FITUR BARU: SATPAM DIGITAL (LOGIN)
# ==========================================
st.title("🔒 Portal Akses Karyawan")
password_input = st.text_input("Masukkan Password Rahasia:", type="password")

# Cek apakah password salah
if password_input != "bosgudang123":
    # Jika salah (dan kotak tidak kosong), tampilkan pesan error
    if password_input != "":
        st.error("Akses Ditolak! Password salah.")
    
    # PERINTAH MUTLAK: Berhenti di sini! Jangan muat dasbor di bawahnya.
    st.stop()

# Jika password benar, layar akan lanjut memuat kode di bawah ini:
st.success("✅ Akses Diterima! Memuat dasbor...")
st.markdown("---")
# ==========================================



# ... dan seterusnya sampai bawah ...
st.title("📦 Dasbor Manajemen Gudang (Versi Alpha)")
st.markdown("---")

# ==========================================
# 1. AMBIL DATA DULU (Agar menu dropdown tahu barang apa saja yang ada)
# ==========================================
koneksi = sqlite3.connect('gudang_kita.db')
data_gudang = pd.read_sql_query("SELECT * FROM Master_Barang", koneksi)
koneksi.close()

# ==========================================
# 2. PANEL KIRI: FITUR BARANG MASUK & KELUAR
# ==========================================
st.sidebar.header("➕ Tambah Barang Baru")
with st.sidebar.form("form_tambah_barang", clear_on_submit=True):
    input_nama = st.text_input("Nama Barang")
    input_beli = st.number_input("Harga Beli (Rp)", min_value=0, step=1000)
    input_jual = st.number_input("Harga Jual (Rp)", min_value=0, step=1000)
    input_stok = st.number_input("Jumlah Stok", min_value=0, step=1)
    
    if st.form_submit_button("Simpan ke Database"):
        koneksi = sqlite3.connect('gudang_kita.db')
        kurir = koneksi.cursor()
        kurir.execute('''
            INSERT INTO Master_Barang (nama_barang, harga_beli, harga_jual, stok)
            VALUES (?, ?, ?, ?)
        ''', (input_nama, input_beli, input_jual, input_stok))
        koneksi.commit()
        koneksi.close()
        st.sidebar.success("Barang berhasil ditambahkan!")
        st.rerun() # Memaksa layar web memuat ulang seketika

st.sidebar.markdown("---")

# FITUR BARU: BARANG KELUAR (KASIR)
st.sidebar.header("➖ Barang Keluar (Kasir)")

# Mengambil daftar nama barang dari Pandas untuk dijadikan menu Dropdown
daftar_nama_barang = data_gudang['nama_barang'].tolist()

with st.sidebar.form("form_barang_keluar", clear_on_submit=True):
    # Membuat menu pilihan (Dropdown)
    barang_dipilih = st.selectbox("Pilih Barang yang Keluar", daftar_nama_barang)
    jumlah_keluar = st.number_input("Jumlah Keluar", min_value=1, step=1)
    
    if st.form_submit_button("Kurangi Stok"):
        # Cek dulu sisa stok saat ini menggunakan kekuatan Pandas
        stok_saat_ini = data_gudang.loc[data_gudang['nama_barang'] == barang_dipilih, 'stok'].values[0]
        
        # Logika Keamanan: Jangan sampai minus!
        if jumlah_keluar > stok_saat_ini:
            st.sidebar.error(f"GAGAL! Stok {barang_dipilih} hanya sisa {stok_saat_ini}.")
        else:
            # Jika stok cukup, perbarui brankas (UPDATE)
            koneksi = sqlite3.connect('gudang_kita.db')
            kurir = koneksi.cursor()
            kurir.execute('''
                UPDATE Master_Barang 
                SET stok = stok - ? 
                WHERE nama_barang = ?
            ''', (jumlah_keluar, barang_dipilih))
            koneksi.commit()
            koneksi.close()
            
            st.sidebar.success(f"Berhasil mengeluarkan {jumlah_keluar} {barang_dipilih}!")
            st.rerun() # Memaksa layar web memuat ulang seketika

# ==========================================
# 3. MENGHITUNG METRIK & MENAMPILKAN VISUAL UTAMA
# ==========================================
# (Kita harus mengambil data lagi karena mungkin brankas baru saja diperbarui oleh fitur di atas)
koneksi = sqlite3.connect('gudang_kita.db')
data_gudang_terbaru = pd.read_sql_query("SELECT * FROM Master_Barang", koneksi)
koneksi.close()

data_gudang_terbaru['Total_Nilai_Aset'] = data_gudang_terbaru['harga_beli'] * data_gudang_terbaru['stok']
total_aset_rupiah = data_gudang_terbaru['Total_Nilai_Aset'].sum()

st.subheader("Ringkasan Keuangan")
st.metric(label="Total Nilai Aset Gudang", value=f"Rp {total_aset_rupiah:,.0f}")
st.write("")

kolom_kiri, kolom_kanan = st.columns(2)

with kolom_kiri:
    st.subheader("📋 Tabel Stok Interaktif")
    st.dataframe(data_gudang_terbaru[['nama_barang', 'harga_beli', 'stok', 'Total_Nilai_Aset']], use_container_width=True)

with kolom_kanan:
    st.subheader("📊 Grafik Stok Barang")
    st.bar_chart(data_gudang_terbaru.set_index('nama_barang')['stok'])

    # ==========================================
# 5. FITUR EKSPOR (DOWNLOAD KE EXCEL/CSV)
# ==========================================
st.markdown("---")
st.subheader("🖨️ Cetak Laporan")

# Pandas menyulap tabel memori menjadi format CSV (format universal yang disukai Excel)
data_csv = data_gudang_terbaru.to_csv(index=False).encode('utf-8')

# Streamlit merakit tombol fisik di layar web untuk mengunduhnya
st.download_button(
    label="📥 Download Data Gudang (Excel/CSV)",
    data=data_csv,
    file_name="Laporan_Stok_Gudang.csv",
    mime="text/csv"
)
