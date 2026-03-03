import sqlite3

# 1. Membuat brankas baru (atau membuka jika sudah ada)
koneksi = sqlite3.connect('gudang_kita.db')

# 2. Memanggil 'kurir' untuk menjalankan perintah SQL
kurir = koneksi.cursor()

# 3. Menulis perintah SQL untuk membuat Tabel (Rak Barang)
kurir.execute('''
    CREATE TABLE IF NOT EXISTS Master_Barang (
        id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_barang TEXT,
        harga_beli INTEGER,
        harga_jual INTEGER,
        stok INTEGER
    )
''')

# 4. Mengunci perubahan brankas dan menutup pintu
koneksi.commit()
koneksi.close()

print("Misi Berhasil: Brankas Gudang dan Tabel Master Barang sudah siap!")