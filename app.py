import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Nilai Tesis Kimia UGM", layout="wide")

# --- KONEKSI DATABASE ---
# Koneksi ini akan membaca konfigurasi [connections.gsheets] dari Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Membaca 3 tab utama: mahasiswa, dosen, nilai
        df_mhs = conn.read(worksheet="mahasiswa", ttl=0)
        df_dosen = conn.read(worksheet="dosen", ttl=0)
        
        try:
            df_rekap = conn.read(worksheet="nilai", ttl=0)
        except Exception:
            # Jika tab 'nilai' baru dibuat dan masih kosong
            df_rekap = pd.DataFrame(columns=["Timestamp", "NIM", "Nama", "Dosen", "Peran", "Rerata"])
            
        return df_mhs, df_dosen, df_rekap
    except Exception as e:
        st.error(f"❌ Koneksi Gagal: {e}")
        st.info("Pastikan di Secrets hanya berisi [connections.gsheets] dan URL yang benar.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mhs, df_dosen, df_rekap = load_data()

# --- SIDEBAR ---
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Menu:", ["📝 Input Nilai", "📊 Rekap Admin"])

if menu == "📝 Input Nilai":
    st.title("📝 Form Penilaian Tesis")
    
    if not df_mhs.empty and not df_dosen.empty:
        col1, col2 = st.columns(2)
        with col1:
            # Menggunakan .astype(str) untuk menghindari error tipe data
            list_mhs = df_mhs["Nama"].dropna().unique().tolist()
            pilih_mhs = st.selectbox("Pilih Mahasiswa", list_mhs)
            
            data_mhs = df_mhs[df_mhs["Nama"] == pilih_mhs].iloc[0]
            nim_mhs = data_mhs["NIM"]
            st.info(f"**NIM:** {nim_mhs}")
            
        with col2:
            list_dosen = df_dosen["Nama_Dosen"].dropna().unique().tolist()
            dosen_pengisi = st.selectbox("Nama Dosen Penilai", list_dosen)
            peran = st.radio("Peran", ["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II"], horizontal=True)

        with st.form("form_n"):
            st.subheader(f"Rubrik: {peran}")
            c_a, c_b = st.columns(2)
            if "Pembimbing" in peran:
                with c_a:
                    n1 = st.number_input("Ketrampilan Kerja", 3.0, 4.0, 3.5)
                    n2 = st.number_input("Penalaran", 3.0, 4.0, 3.5)
                    n3 = st.number_input("Kesanggupan Kerja", 3.0, 4.0, 3.5)
                with c_b:
                    n4 = st.number_input("Format Penulisan", 3.0, 4.0, 3.5)
                    n5 = st.number_input("Presentasi Data", 3.0, 4.0, 3.5)
            else:
                with c_a:
                    n1 = st.number_input("Format Penulisan", 3.0, 4.0, 3.5)
                    n2 = st.number_input("Kualitas Data", 3.0, 4.0, 3.5)
                    n3 = st.number_input("Presentasi Lisan", 3.0, 4.0, 3.5)
                with c_b:
                    n4 = st.number_input("Penguasaan Materi", 3.0, 4.0, 3.5)
                    n5 = st.number_input("Kualitas Penalaran", 3.0, 4.0, 3.5)

            if st.form_submit_button("Simpan Nilai", type="primary"):
                rerata = (n1+n2+n3+n4+n5)/5
                new_data = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NIM": str(nim_mhs),
                    "Nama": pilih_mhs,
                    "Dosen": dosen_pengisi,
                    "Peran": peran,
                    "Rerata": rerata
                }])
                try:
                    df_final = pd.concat([df_rekap, new_data], ignore_index=True)
                    conn.update(worksheet="nilai", data=df_final)
                    st.success("✅ Nilai Berhasil Disimpan!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Gagal Simpan: {e}")
    else:
        st.warning("Data mahasiswa atau dosen kosong.")

elif menu == "📊 Rekap Admin":
    st.title("📊 Rekapitulasi Nilai")
    if st.sidebar.text_input("Password", type="password") == "kimia123":
        if not df_rekap.empty:
            # Proses Pivot
            df_p = df_rekap.pivot_table(index=["NIM", "Nama"], columns="Peran", values="Rerata", aggfunc='last').reset_index()
            # Gabung dengan Seminar
            if "Seminar" in df_mhs.columns:
                df_res = pd.merge(df_p, df_mhs[["NIM", "Seminar"]], on="NIM", how="left")
                st.dataframe(df_res, use_container_width=True)
            else:
                st.dataframe(df_p, use_container_width=True)
        else:
            st.info("Belum ada data nilai.")
