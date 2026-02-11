import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Nilai Tesis Kimia UGM", layout="wide", page_icon="🧪")

# --- KONEKSI DATABASE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Membaca 3 Tab Utama
        mhs = conn.read(worksheet="Daftar_Mahasiswa", ttl=2)
        dosen = conn.read(worksheet="Daftar_Dosen", ttl=2)
        try:
            rekap = conn.read(worksheet="Rekap_Nilai", ttl=2)
        except:
            # Jika tab Rekap_Nilai masih benar-benar kosong (tanpa header)
            rekap = pd.DataFrame(columns=["Timestamp", "NIM", "Nama", "Dosen", "Peran", "Rerata"])
        return mhs, dosen, rekap
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets. Cek nama Tab atau koneksi Secrets. Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mhs, df_dosen, df_rekap = load_data()

# --- SIDEBAR NAVIGASI ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/2/25/Logougm.png", width=100)
st.sidebar.title("Menu Utama")
menu = st.sidebar.radio("Pilih Halaman:", ["📝 Input Nilai Dosen", "📊 Rekapitulasi Akhir (Admin)"])

# ==============================================================================
# HALAMAN 1: INPUT NILAI DOSEN
# ==============================================================================
if menu == "📝 Input Nilai Dosen":
    st.title("📝 Form Penilaian Ujian Tesis")
    st.info("Nilai hanya akan tersimpan setelah Anda menekan tombol **'Kirim Nilai Final'** di bawah.")

    # Inisialisasi variabel untuk mencegah NameError
    dosen_pengisi = ""
    peran = ""
    nim = ""
    pilih_mhs = ""

    # Bagian 1: Pilih Identitas
    c_identitas1, c_identitas2 = st.columns(2)
    
    with c_identitas1:
        if not df_mhs.empty:
            pilih_mhs = st.selectbox("Pilih Nama Mahasiswa", df_mhs["Nama"].tolist())
            data_mhs = df_mhs[df_mhs["Nama"] == pilih_mhs].iloc[0]
            nim = data_mhs["NIM"]
            st.success(f"**NIM:** {nim}  \n**Judul:** {data_mhs['Judul']}")
        else:
            st.warning("Data mahasiswa tidak ditemukan di Google Sheets.")

    with c_identitas2:
        if not df_dosen.empty:
            dosen_pengisi = st.selectbox("Pilih Nama Anda (Dosen)", df_dosen["Nama_Dosen"].tolist())
            peran = st.radio("Peran dalam Ujian:", ["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II"], horizontal=True)
        else:
            st.warning("Data dosen tidak ditemukan.")

    st.divider()

    # Bagian 2: Form Input Nilai
    if pilih_mhs and dosen_pengisi:
        with st.form("form_nilai"):
            st.subheader(f"Rubrik Penilaian untuk: {peran}")
            
            col_a, col_b = st.columns(2)
            
            if "Pembimbing" in peran:
                with col_a:
                    v1 = st.number_input("1. Ketrampilan & Ketelitian Kerja", 3.0, 4.0, 3.5, 0.1)
                    v2 = st.number_input("2. Penalaran memecahkan masalah", 3.0, 4.0, 3.5, 0.1)
                    v3 = st.number_input("3. Kesanggupan kerja / Usaha keras", 3.0, 4.0, 3.5, 0.1)
                with col_b:
                    v4 = st.number_input("4. Kesesuaian format & kecermatan penulisan", 3.0, 4.0, 3.5, 0.1)
                    v5 = st.number_input("5. Kualitas presentasi data & pembahasan", 3.0, 4.0, 3.5, 0.1)
            else:
                with col_a:
                    v1 = st.number_input("1. Kesesuaian format & kecermatan penulisan", 3.0, 4.0, 3.5, 0.1)
                    v2 = st.number_input("2. Kualitas presentasi data & pembahasan", 3.0, 4.0, 3.5, 0.1)
                    v3 = st.number_input("3. Kemampuan presentasi lisan", 3.0, 4.0, 3.5, 0.1)
                with col_b:
                    v4 = st.number_input("4. Penguasaan materi", 3.0, 4.0, 3.5, 0.1)
                    v5 = st.number_input("5. Kualitas penalaran", 3.0, 4.0, 3.5, 0.1)

            submit_btn = st.form_submit_button("Kirim Nilai Final", type="primary")

            if submit_btn:
                rerata = (v1 + v2 + v3 + v4 + v5) / 5
                
                # Buat baris data baru
                data_baru = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NIM": nim,
                    "Nama": pilih_mhs,
                    "Dosen": dosen_pengisi,
                    "Peran": peran,
                    "Rerata": rerata
                }])
                
                try:
                    # Update data ke tab Rekap_Nilai
                    updated_df = pd.concat([df_rekap, data_baru], ignore_index=True)
                    conn.update(worksheet="Rekap_Nilai", data=updated_df)
                    st.balloons()
                    st.success(f"✅ Nilai Rerata {rerata:.2f} dari {dosen_pengisi} berhasil disimpan!")
                except Exception as e:
                    st.error(f"Gagal menyimpan ke Google Sheets: {e}")

# ==============================================================================
# HALAMAN 2: REKAPITULASI AKHIR (ADMIN)
# ==============================================================================
elif menu == "📊 Rekapitulasi Akhir (Admin)":
    st.title("📊 Rekapitulasi & Perhitungan Nilai Akhir")
    
    pwd = st.sidebar.text_input("Masukkan Password Admin", type="password")
    
    if pwd == "kimia123": # <--- Ganti password Anda di sini
        if df_rekap.empty:
            st.info("Belum ada data nilai yang masuk di tab 'Rekap_Nilai'.")
        else:
            # 1. Transformasi Data (Pivot) agar 1 mahasiswa = 1 baris
            rekap_pivot = df_rekap.sort_values("Timestamp").pivot_table(
                index=["NIM", "Nama"], 
                columns="Peran", 
                values="Rerata", 
                aggfunc='last'
            ).reset_index()

            # 2. Ambil Nilai Seminar dari Tab Daftar_Mahasiswa
            rekap_final = pd.merge(rekap_pivot, df_mhs[["NIM", "Seminar"]], on="NIM", how="left")

            # 3. Fungsi Hitung Bobot & Huruf
            def kalkulasi(row):
                sem = row.get("Seminar", 0)
                p1 = row.get("Pembimbing I", 0)
                p2 = row.get("Pembimbing II", 0)
                u1 = row.get("Penguji I", 0)
                u2 = row.get("Penguji II", 0)
                
                # Rumus: (Sem*1 + P1*2 + P2*2 + U1*1.5 + U2*1.5) / 8
                total_skor = (sem*1) + (p1*2) + (p2*2) + (u1*1.5) + (u2*1.5)
                return total_skor / 8

            def konversi_huruf(n):
                if n >= 3.81: return "A"
                elif n >= 3.61: return "A-"
                elif n >= 3.41: return "A/B"
                elif n >= 3.21: return "B+"
                elif n >= 3.01: return "B"
                elif n >= 2.00: return "C" # Contoh penambahan
                else: return "Incomplete"

            # 4. Terapkan Perhitungan
            rekap_final["Nilai Akhir"] = rekap_final.apply(kalkulasi, axis=1)
            rekap_final["Predikat"] = rekap_final["Nilai Akhir"].apply(konversi_huruf)

            # Tampilkan Tabel
            st.subheader("Tabel Rekapitulasi Real-time")
            st.dataframe(rekap_final.style.format(precision=2), use_container_width=True)

            # Tombol Download
            csv = rekap_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Hasil (CSV)", csv, "rekap_nilai_kimia.csv", "text/csv")
    else:
        st.warning("Silakan masukkan password admin pada sidebar untuk melihat rekapitulasi.")
