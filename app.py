import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Nilai Tesis Kimia UGM", 
    layout="wide", 
    page_icon="🧪"
)

# --- KONEKSI DATABASE GOOGLE SHEETS ---
# Pastikan di Secrets URL-nya hanya sampai /edit saja
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Load Data Mahasiswa
        df_mhs = conn.read(worksheet="Daftar_Mahasiswa", ttl=0)
        
        # Load Data Dosen
        df_dosen = conn.read(worksheet="Daftar_Dosen", ttl=0)
        
        # Load Data Rekap (Gunakan try-except jika tab kosong/error)
        try:
            df_rekap = conn.read(worksheet="Rekap_Nilai", ttl=0)
        except Exception:
            # Jika tab Rekap_Nilai tidak ditemukan/kosong, buat DataFrame kosong dengan kolom yang benar
            df_rekap = pd.DataFrame(columns=["Timestamp", "NIM", "Nama", "Dosen", "Peran", "Rerata"])
            
        return df_mhs, df_dosen, df_rekap
    except Exception as e:
        st.error(f"❌ Gagal Memuat Spreadsheet: {e}")
        st.info("Pastikan: 1. Nama Tab benar, 2. URL di Secrets benar, 3. Akses Google Sheet sudah 'Anyone with link' sebagai Editor.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Menjalankan fungsi load data
df_mhs, df_dosen, df_rekap = load_data()

# --- SIDEBAR ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/2/25/Logougm.png", width=80)
st.sidebar.title("Sistem Penilaian")
menu = st.sidebar.radio("Navigasi", ["📝 Input Nilai Dosen", "📊 Rekap Admin"])

# ==============================================================================
# HALAMAN 1: INPUT NILAI DOSEN
# ==============================================================================
if menu == "📝 Input Nilai Dosen":
    st.title("📝 Form Penilaian Ujian Tesis")
    
    if df_mhs.empty or df_dosen.empty:
        st.error("Data Mahasiswa atau Dosen tidak ditemukan. Periksa Google Sheets Anda.")
    else:
        # 1. Identitas
        c1, c2 = st.columns(2)
        with c1:
            pilih_mhs = st.selectbox("Pilih Mahasiswa", df_mhs["Nama"].tolist())
            row_mhs = df_mhs[df_mhs["Nama"] == pilih_mhs].iloc[0]
            nim_mhs = row_mhs["NIM"]
            st.success(f"**NIM:** {nim_mhs}  \n**Judul:** {row_mhs.get('Judul', '-')}")
        
        with c2:
            dosen_pengisi = st.selectbox("Nama Dosen Penilai", df_dosen["Nama_Dosen"].tolist())
            peran = st.radio("Peran Anda", ["Pembimbing I", "Pembimbing II", "Penguji I", "Penguji II"], horizontal=True)

        st.divider()

        # 2. Form Input
        with st.form("form_penilaian"):
            st.subheader(f"Rubrik: {peran}")
            col_a, col_b = st.columns(2)
            
            if "Pembimbing" in peran:
                with col_a:
                    v1 = st.number_input("1. Ketrampilan & Ketelitian Kerja", 3.0, 4.0, 3.5, 0.1)
                    v2 = st.number_input("2. Penalaran memecahkan masalah", 3.0, 4.0, 3.5, 0.1)
                    v3 = st.number_input("3. Kesanggupan kerja / Usaha keras", 3.0, 4.0, 3.5, 0.1)
                with col_b:
                    v4 = st.number_input("4. Format & kecermatan penulisan", 3.0, 4.0, 3.5, 0.1)
                    v5 = st.number_input("5. Presentasi data & pembahasan", 3.0, 4.0, 3.5, 0.1)
            else:
                with col_a:
                    v1 = st.number_input("1. Format & kecermatan penulisan", 3.0, 4.0, 3.5, 0.1)
                    v2 = st.number_input("2. Kualitas presentasi data & pembahasan", 3.0, 4.0, 3.5, 0.1)
                    v3 = st.number_input("3. Kemampuan presentasi lisan", 3.0, 4.0, 3.5, 0.1)
                with col_b:
                    v4 = st.number_input("4. Penguasaan materi", 3.0, 4.0, 3.5, 0.1)
                    v5 = st.number_input("5. Kualitas penalaran", 3.0, 4.0, 3.5, 0.1)

            btn_submit = st.form_submit_button("Kirim Nilai Final", type="primary")

            if btn_submit:
                rerata_nilai = (v1+v2+v3+v4+v5)/5
                data_baru = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NIM": nim_mhs,
                    "Nama": pilih_mhs,
                    "Dosen": dosen_pengisi,
                    "Peran": peran,
                    "Rerata": rerata_nilai
                }])
                
                try:
                    # Gabungkan data lama dengan data baru
                    df_update = pd.concat([df_rekap, data_baru], ignore_index=True)
                    conn.update(worksheet="Rekap_Nilai", data=df_update)
                    st.balloons()
                    st.success(f"✅ Berhasil! Nilai {rerata_nilai:.2f} tersimpan.")
                except Exception as e:
                    st.error(f"Gagal menyimpan ke Google Sheets: {e}")

# ==============================================================================
# HALAMAN 2: REKAPITULASI (ADMIN)
# ==============================================================================
elif menu == "📊 Rekap Admin":
    st.title("📊 Rekapitulasi & Nilai Akhir")
    pw = st.sidebar.text_input("Password Admin", type="password")
    
    if pw == "kimia123":
        if df_rekap.empty:
            st.info("Belum ada data nilai di tab 'Rekap_Nilai'.")
        else:
            # Pivot data: 1 baris per Mahasiswa
            df_pivot = df_rekap.pivot_table(
                index=["NIM", "Nama"], 
                columns="Peran", 
                values="Rerata", 
                aggfunc='last'
            ).reset_index()
            
            # Gabungkan dengan nilai Seminar dari tab Daftar_Mahasiswa
            if "Seminar" in df_mhs.columns:
                df_final = pd.merge(df_pivot, df_mhs[["NIM", "Seminar"]], on="NIM", how="left")
                
                # Fungsi Hitung Bobot 8
                def hitung_skor(row):
                    s = row.get("Seminar", 0)
                    p1 = row.get("Pembimbing I", 0)
                    p2 = row.get("Pembimbing II", 0)
                    u1 = row.get("Penguji I", 0)
                    u2 = row.get("Penguji II", 0)
                    return ((s*1) + (p1*2) + (p2*2) + (u1*1.5) + (u2*1.5)) / 8
                
                def get_huruf(n):
                    if n >= 3.81: return "A"
                    elif n >= 3.61: return "A-"
                    elif n >= 3.41: return "A/B"
                    elif n >= 3.21: return "B+"
                    elif n >= 3.01: return "B"
                    else: return "C/Incomplete"

                df_final["Nilai Akhir"] = df_final.apply(hitung_skor, axis=1)
                df_final["Huruf"] = df_final["Nilai Akhir"].apply(get_huruf)
                
                st.dataframe(df_final.style.format(precision=2), use_container_width=True)
            else:
                st.warning("Kolom 'Seminar' tidak ditemukan di tab Daftar_Mahasiswa.")
                st.dataframe(df_pivot)
    else:
        st.warning("Masukkan password untuk melihat rekap.")
