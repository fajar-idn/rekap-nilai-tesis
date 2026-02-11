import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Penilaian Tesis Kimia", layout="wide")

# --- KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi Membaca Data (Cache 5 detik agar update cepat)
def load_data():
    try:
        # Pastikan nama worksheet sesuai dengan tab di Google Sheets Anda
        mhs = conn.read(worksheet="Daftar_Mahasiswa", ttl=5)
        dosen = conn.read(worksheet="Daftar_Dosen", ttl=5)
        # Handle jika Rekap_Nilai masih kosong
        try:
            rekap = conn.read(worksheet="Rekap_Nilai", ttl=5)
        except:
            rekap = pd.DataFrame(columns=["Timestamp", "NIM", "Nama", "Dosen", "Peran", "Rerata"])
        return mhs, dosen, rekap
    except Exception as e:
        st.error(f"Gagal memuat data. Pastikan Google Sheets sudah disetting public/secrets benar. Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mhs, df_dosen, df_rekap = load_data()

# --- SIDEBAR: NAVIGASI ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/2/25/Logougm.png", width=100)
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Menu:", ["📝 Input Nilai Dosen", "📊 Rekapitulasi Akhir (Admin)"])

# ==============================================================================
# MENU 1: INPUT NILAI (Tampilan untuk Dosen)
# ==============================================================================
if menu == "📝 Input Nilai Dosen":
    st.title("📝 Form Penilaian Ujian Tesis")
    st.info("Silakan isi penilaian di bawah ini. Nilai baru akan tersimpan setelah tombol **Kirim** ditekan.")

    # 1. Identitas
    col1, col2 = st.columns(2)
    with col1:
        if not df_mhs.empty:
            pilih_mhs = st.selectbox("Pilih Mahasiswa", df_mhs["Nama"].tolist())
            row_mhs = df_mhs[df_mhs["Nama"] == pilih_mhs].iloc[0]
            nim = row_mhs["NIM"]
            st.caption(f"Judul: {row_mhs['Judul']}")
        else:
            st.warning("Database Mahasiswa Kosong")
            pilih_mhs = "Unknown"
            nim = "-"

    with col2:
        if not df_dosen.empty:
            dosen_pengisi = st.selectbox("Nama Dosen Penilai", df_dosen["Nama_Dosen"].tolist())
            peran = st.radio("Peran Anda", ["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II"], horizontal=True)
        else:
            st.warning("Database Dosen Kosong")

    st.divider()

    # 2. Form Input (Dalam Container Form)
    # Apapun yang diubah di sini TIDAK akan reload halaman sampai tombol ditekan
    with st.form("form_penilaian"):
        st.subheader(f"Rubrik Penilaian: {peran}")
        
        c1, c2 = st.columns(2)
        # Logika Rubrik (Pembimbing vs Penguji)
        if "Pembimbing" in peran:
            with c1:
                v1 = st.number_input("1. Ketrampilan & Ketelitian (Lab/Riset)", 3.0, 4.0, 3.5, 0.1)
                v2 = st.number_input("2. Penalaran & Pemecahan Masalah", 3.0, 4.0, 3.5, 0.1)
                v3 = st.number_input("3. Kesanggupan Kerja (Usaha)", 3.0, 4.0, 3.5, 0.1)
            with c2:
                v4 = st.number_input("4. Format & Kecermatan Tulisan", 3.0, 4.0, 3.5, 0.1)
                v5 = st.number_input("5. Presentasi Data & Pembahasan", 3.0, 4.0, 3.5, 0.1)
        else:
            with c1:
                v1 = st.number_input("1. Format & Kecermatan Tulisan", 3.0, 4.0, 3.5, 0.1)
                v2 = st.number_input("2. Kualitas Data & Pembahasan", 3.0, 4.0, 3.5, 0.1)
                v3 = st.number_input("3. Kemampuan Presentasi Lisan", 3.0, 4.0, 3.5, 0.1)
            with c2:
                v4 = st.number_input("4. Penguasaan Materi", 3.0, 4.0, 3.5, 0.1)
                v5 = st.number_input("5. Kualitas Penalaran", 3.0, 4.0, 3.5, 0.1)

        # Tombol Submit
        submitted = st.form_submit_button("Kirim Nilai Final")

        if submitted:
            # Hitung Rerata
            rerata_akhir = (v1 + v2 + v3 + v4 + v5) / 5
            
            # Siapkan Data
            waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_baru = pd.DataFrame([{
                "Timestamp": waktu,
                "NIM": nim,
                "Nama": pilih_mhs,
                "Dosen": dosen_pengisi,
                "Peran": peran,
                "Rerata": rerata_akhir
            }])
            
            # Simpan ke Google Sheets (Append)
            # Catatan: Library ini otomatis append jika data dikirim ke sheet yang sama
            try:
                # Menggabungkan data lama dengan data baru
                updated_df = pd.concat([df_rekap, data_baru], ignore_index=True)
                conn.update(worksheet="Rekap_Nilai", data=updated_df)
                st.success(f"✅ Terima kasih {dosen_pengisi}, nilai {rerata_akhir:.2f} berhasil disimpan!")
            except Exception as e:
                st.error(f"Gagal menyimpan: {e}")

# ==============================================================================
# MENU 2: REKAPITULASI (Khusus Admin/Ketua Penguji)
# ==============================================================================
elif menu == "📊 Rekapitulasi Akhir (Admin)":
    st.title("📊 Rekapitulasi Nilai Akhir")
    
    # Fitur Keamanan Sederhana
    password = st.sidebar.text_input("Masukkan Password Admin", type="password")
    
    if password == "kimia123": # Ganti password sesuai keinginan
        if df_rekap.empty:
            st.warning("Belum ada data nilai yang masuk.")
        else:
            # --- PROSES PIVOT TABLE UNTUK REKAP ---
            # Kita ubah data memanjang menjadi melebar (Satu baris per mahasiswa)
            # Ambil nilai terakhir (jika dosen submit 2x, ambil yang terbaru)
            df_rekap_sorted = df_rekap.sort_values(by="Timestamp", ascending=True)
            
            # Pivot: Baris=NIM, Kolom=Peran, Isi=Rerata
            rekap_final = df_rekap_sorted.pivot_table(
                index=["NIM", "Nama"], 
                columns="Peran", 
                values="Rerata", 
                aggfunc='last' # Ambil entri terakhir
            ).reset_index()

            # Pastikan semua kolom ada (cegah error jika belum lengkap)
            required_cols = ["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II"]
            for col in required_cols:
                if col not in rekap_final.columns:
                    rekap_final[col] = 0 # Isi 0 jika belum ada nilai

            # --- RUMUS HITUNG NILAI AKHIR ---
            # Rumus: (Sem*1 + P1*2 + P2*2 + U1*1.5 + U2*1.5) / 8
            # Note: Nilai seminar (Sem) diasumsikan sudah ada (misal default 3.5 atau ambil dari sheet lain)
            nilai_seminar = 3.5 # SEMENTARA (Bisa diambil dari kolom database jika ada)
            
            def hitung_bobot(row):
                total = (nilai_seminar * 1) + \
                        (row["Pembimbing I"] * 2) + \
                        (row["Pembimbing II"] * 2) + \
                        (row["Penguji I"] * 1.5) + \
                        (row["Penguji II"] * 1.5)
                return total / 8

            rekap_final["Nilai Akhir"] = rekap_final.apply(hitung_bobot, axis=1)

            # --- KONVERSI HURUF ---
            def get_huruf(n):
                if n >= 3.81: return "A"
                elif n >= 3.61: return "A-"
                elif n >= 3.41: return "A/B"
                elif n >= 3.21: return "B+"
                elif n >= 3.01: return "B"
                else: return "Belum Lulus / Data Tidak Lengkap"

            rekap_final["Predikat"] = rekap_final["Nilai Akhir"].apply(get_huruf)

            # Tampilkan Tabel
            st.write("Berikut adalah rekapitulasi real-time:")
            st.dataframe(rekap_final.style.format("{:.2f}", subset=["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II", "Nilai Akhir"]))
            
            # Tombol Download Excel
            st.download_button(
                label="📥 Download Rekap Excel",
                data=rekap_final.to_csv(index=False).encode('utf-8'),
                file_name='rekap_nilai_tesis.csv',
                mime='text/csv',
            )
            
    else:
        st.warning("Menu ini hanya untuk Ketua Penguji/Admin. Masukkan password di sidebar.")
