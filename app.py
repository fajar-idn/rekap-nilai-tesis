import streamlit as st
import pandas as pd

# Judul Aplikasi
st.set_page_config(page_title="Sistem Rekap Nilai Tesis", layout="wide")
st.title("🎓 Sistem Rekapitulasi Nilai Ujian Tesis")
st.write("Berdasarkan Format Berita Acara Magister Kimia")

# --- BAGIAN 1: IDENTITAS MAHASISWA ---
st.header("1. Identitas Mahasiswa")
col1, col2 = st.columns(2)
with col1:
    nama = st.text_input("Nama Mahasiswa", "Lili Tata")
    nim = st.text_input("NIM", "23/511872/PPA/06493")
with col2:
    prodi = st.text_input("Program Studi", "Magister Kimia")
    judul = st.text_area("Judul Tesis", "SINTESIS KOMPOSIT ZIF-8/KARBON AKTIF...")

st.divider()

# --- BAGIAN 2: INPUT NILAI PER KOMPONEN ---
st.header("2. Input Nilai Dosen (Skala 3.0 - 4.0)")

# Fungsi untuk membuat input angka dengan rentang 3.0 - 4.0
def input_nilai(label):
    return st.number_input(label, min_value=3.0, max_value=4.0, value=3.5, step=0.1)

# Kolom untuk Seminar dan Pembimbing
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Admin & Pembimbing")
    n_seminar = st.number_input("1. Nilai Seminar Tesis (Bobot 1)", 3.0, 4.0, 3.5, 0.1)
    
    with st.expander("2. Nilai Penelitian - Pembimbing I"):
        # Rubrik Penelitian 
        p1_a1 = input_nilai("P1: Keterampilan & Ketelitian")
        p1_a2 = input_nilai("P1: Penalaran & Pengembangan")
        p1_a3 = input_nilai("P1: Kesanggupan Kerja")
        p1_b1 = input_nilai("P1: Format & Kecermatan Tulisan")
        p1_b2 = input_nilai("P1: Kualitas Presentasi & Pembahasan")
        rerata_p1 = (p1_a1 + p1_a2 + p1_a3 + p1_b1 + p1_b2) / 5

    with st.expander("3. Nilai Penelitian - Pembimbing II"):
        p2_a1 = input_nilai("P2: Keterampilan & Ketelitian")
        p2_a2 = input_nilai("P2: Penalaran & Pengembangan")
        p2_a3 = input_nilai("P2: Kesanggupan Kerja")
        p2_b1 = input_nilai("P2: Format & Kecermatan Tulisan")
        p2_b2 = input_nilai("P2: Kualitas Presentasi & Pembahasan")
        rerata_p2 = (p2_a1 + p2_a2 + p2_a3 + p2_b1 + p2_b2) / 5

with col_b:
    st.subheader("Penguji")
    with st.expander("4. Nilai Ujian - Penguji I"):
        # Rubrik Ujian 
        u1_a1 = input_nilai("U1: Format & Kecermatan Tulisan")
        u1_a2 = input_nilai("U1: Kualitas Data & Pembahasan")
        u1_b1 = input_nilai("U1: Kemampuan Presentasi")
        u1_b2 = input_nilai("U1: Penguasaan Materi")
        u1_b3 = input_nilai("U1: Kualitas Penalaran")
        rerata_u1 = (u1_a1 + u1_a2 + u1_b1 + u1_b2 + u1_b3) / 5

    with st.expander("5. Nilai Ujian - Penguji II"):
        u2_a1 = input_nilai("U2: Format & Kecermatan Tulisan")
        u2_a2 = input_nilai("U2: Kualitas Data & Pembahasan")
        u2_b1 = input_nilai("U2: Kemampuan Presentasi")
        u2_b2 = input_nilai("U2: Penguasaan Materi")
        u2_b3 = input_nilai("U2: Kualitas Penalaran")
        rerata_u2 = (u2_a1 + u2_a2 + u2_b1 + u2_b2 + u2_b3) / 5

# --- BAGIAN 3: KALKULASI AKHIR ---
st.divider()
if st.button("HITUNG REKAPITULASI AKHIR", type="primary"):
    # Rumus Bobot 
    # Total Bobot = 1 + 2 + 2 + 1.5 + 1.5 = 8
    total_poin = (n_seminar * 1) + (rerata_p1 * 2) + (rerata_p2 * 2) + (rerata_u1 * 1.5) + (rerata_u2 * 1.5)
    nilai_akhir = total_poin / 8

    # Penentuan Huruf 
    if nilai_akhir >= 3.81: huruf = "A"
    elif nilai_akhir >= 3.61: huruf = "A-"
    elif nilai_akhir >= 3.41: huruf = "A/B"
    elif nilai_akhir >= 3.21: huruf = "B+"
    elif nilai_akhir >= 3.01: huruf = "B"
    else: huruf = "Tidak Lulus"

    # Tampilan Hasil
    st.success(f"### Nilai Akhir Angka: {nilai_akhir:.2f}")
    st.info(f"### Predikat Nilai Huruf: {huruf}")

    # Tabel Rekap untuk Laporan
    data_rekap = {
        "Komponen": ["Seminar Tesis", "Penelitian P1", "Penelitian P2", "Ujian U1", "Ujian U2"],
        "Rerata Nilai": [n_seminar, rerata_p1, rerata_p2, rerata_u1, rerata_u2],
        "Bobot": [1, 2, 2, 1.5, 1.5],
        "Nilai * Bobot": [n_seminar*1, rerata_p1*2, rerata_p2*2, rerata_u1*1.5, rerata_u2*1.5]
    }

    st.table(pd.DataFrame(data_rekap))
