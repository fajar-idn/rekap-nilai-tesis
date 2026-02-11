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
        # Membaca data dengan TTL rendah agar update cepat terlihat
        mhs = conn.read(worksheet="Daftar_Mahasiswa", ttl="1s")
        dosen = conn.read(worksheet="Daftar_Dosen", ttl="1s")
        try:
            rekap = conn.read(worksheet="Rekap_Nilai", ttl="1s")
        except:
            rekap = pd.DataFrame(columns=["Timestamp", "NIM", "Nama", "Dosen", "Peran", "Rerata"])
        return mhs, dosen, rekap
    except Exception as e:
        # Menampilkan pesan error detail jika koneksi gagal
        st.error(f"Gagal memuat data dari Google Sheets. Pastikan URL di Secrets benar dan tab 'Daftar_Mahasiswa' serta 'Daftar_Dosen' tersedia. Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mhs, df_dosen, df_rekap = load_data()

# --- SIDEBAR NAVIGASI ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/2/25/Logougm.png", width=100)
st.sidebar.title("Sistem Penilaian")
menu = st.sidebar.radio("Pilih Halaman:", ["📝 Input Nilai Dosen", "📊 Rekapitulasi Akhir (Admin)"])

# ==============================================================================
# HALAMAN 1: INPUT NILAI DOSEN
# ==============================================================================
if menu == "📝 Input Nilai Dosen":
    st.title("📝 Form Penilaian Ujian Tesis")
    st.info("Pilih nama mahasiswa dan nama Anda untuk memulai penilaian.")

    if df_mhs.empty or df_dosen.empty:
        st.warning("⚠️ Data Mahasiswa atau Dosen tidak dapat dimuat. Periksa Google Sheets Anda.")
    else:
        # Bagian 1: Identitas
        c1, c2 = st.columns(2)
        with c1:
            pilih_mhs = st.selectbox("Pilih Nama Mahasiswa", df_mhs["Nama"].tolist())
            data_mhs = df_mhs[df_mhs["Nama"] == pilih_mhs].iloc[0]
            nim = data_mhs["NIM"]
            st.success(f"**NIM:** {nim}  \n**Judul:** {data_mhs['Judul']}")
        
        with c2:
            dosen_pengisi = st.selectbox("Pilih Nama Anda (Dosen)", df_dosen["Nama_Dosen"].tolist())
            peran = st.radio("Peran dalam Ujian:", ["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II"], horizontal=True)

        st.divider()

        # Bagian 2: Form Penilaian
        with st.form("form_nilai"):
            st.subheader(f"Rubrik Penilaian: {peran}")
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
                data_baru = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NIM": nim,
                    "Nama": pilih_mhs,
                    "Dosen": dosen_pengisi,
                    "Peran": peran,
                    "Rerata": rerata
                }])
                
                try:
                    updated_df = pd.concat([df_rekap, data_baru], ignore_index=True)
                    conn.update(worksheet="Rekap_Nilai", data=updated_df)
                    st.balloons()
                    st.success(f"✅ Nilai Rerata {rerata:.2f} berhasil disimpan untuk {pilih_mhs}!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data. Pastikan tab 'Rekap_Nilai' sudah ada. Error: {e}")

# ==============================================================================
# HALAMAN 2: REKAPITULASI (ADMIN)
# ==============================================================================
elif menu == "📊 Rekapitulasi Akhir (Admin)":
    st.title("📊 Rekapitulasi Nilai Akhir")
    pwd = st.sidebar.text_input("Masukkan Password Admin", type="password")
    
    if pwd == "kimia123":
        if df_rekap.empty:
            st.info("Belum ada data nilai yang masuk.")
        else:
            rekap_pivot = df_rekap.pivot_table(index=["NIM", "Nama"], columns="Peran", values="Rerata", aggfunc='last').reset_index()
            rekap_final = pd.merge(rekap_pivot, df_mhs[["NIM", "Seminar"]], on="NIM", how="left")

            def hitung_akhir(row):
                vals = [row.get("Seminar", 0), row.get("Pembimbing I", 0), row.get("Pembimbing II", 0), 
                        row.get("Penguji I", 0), row.get("Penguji II", 0)]
                bobot = [1, 2, 2, 1.5, 1.5]
                return sum(v * b for v, b in zip(vals, bobot)) / 8

            rekap_final["Nilai Akhir"] = rekap_final.apply(hitung_akhir, axis=1)
            st.dataframe(rekap_final.style.format(precision=2), use_container_width=True)
    else:
        st.warning("Masukkan password untuk mengakses data.")
