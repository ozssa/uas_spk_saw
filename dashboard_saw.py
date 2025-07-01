import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Penilaian Karyawan", layout="wide")

# Judul dan deskripsi
st.title("Dashboard Penilaian Karyawan Terbaik (Metode SAW)")
st.markdown("""
**Aplikasi ini menggunakan metode Simple Additive Weighting (SAW) untuk menentukan karyawan terbaik berdasarkan kriteria tertentu.**  
Gunakan sidebar untuk mengatur bobot kriteria dan filter departemen. Hasil peringkat dapat dilihat di tabel dan visualisasi di bawah.
""")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('employee_data.xlsx')
    # Pilih kolom yang relevan
    cols = ['Employee_Name', 'EngagementSurvey', 'EmpSatisfaction', 'SpecialProjectsCount', 'Absences', 'Department']
    df = df[cols].dropna().reset_index(drop=True)
    return df

df = load_data()

# Sidebar untuk pengaturan
st.sidebar.header("Pengaturan SAW")
st.sidebar.markdown("Atur bobot kriteria (jumlah harus = 1)")

# Input bobot
bobot_survey = st.sidebar.slider("Bobot Engagement Survey", 0.0, 1.0, 0.3, 0.05)
bobot_satisfaction = st.sidebar.slider("Bobot Employee Satisfaction", 0.0, 1.0, 0.2, 0.05)
bobot_projects = st.sidebar.slider("Bobot Special Projects Count", 0.0, 1.0, 0.2, 0.05)
bobot_absences = st.sidebar.slider("Bobot Absensi", 0.0, 1.0, 0.3, 0.05)

# Validasi jumlah bobot
total_bobot = bobot_survey + bobot_satisfaction + bobot_projects + bobot_absences
if abs(total_bobot - 1.0) > 0.01:
    st.sidebar.error(f"Jumlah bobot harus 1. Saat ini: {total_bobot:.2f}")
else:
    st.sidebar.success("Bobot valid!")

# Filter departemen
departments = ['All'] + list(df['Department'].unique())
selected_dept = st.sidebar.selectbox("Pilih Departemen", departments)

# Proses data SAW
def calculate_saw(df, bobot):
    X = df[['EngagementSurvey', 'EmpSatisfaction', 'SpecialProjectsCount', 'Absences']].copy()
    # Balik nilai absensi
    X['Absences'] = X['Absences'].max() - X['Absences']
    # Normalisasi
    scaler = MinMaxScaler()
    X_norm = scaler.fit_transform(X)
    # Hitung skor SAW
    skor = X_norm.dot(bobot)
    df['Skor_SAW'] = skor
    df['Ranking'] = df['Skor_SAW'].rank(ascending=False)
    return df.sort_values('Skor_SAW', ascending=False)

# Filter data berdasarkan departemen
if selected_dept != 'All':
    df_filtered = df[df['Department'] == selected_dept].copy()
else:
    df_filtered = df.copy()

# Hitung SAW
if total_bobot == 1.0:
    bobot = np.array([bobot_survey, bobot_satisfaction, bobot_projects, bobot_absences])
    df_result = calculate_saw(df_filtered, bobot)
else:
    df_result = df_filtered.copy()
    st.warning("Harap sesuaikan bobot hingga jumlahnya 1 untuk melihat hasil peringkat.")

# Tampilkan hasil
st.header("Hasil Peringkat Karyawan")
st.dataframe(df_result[['Employee_Name', 'Department', 'EngagementSurvey', 'EmpSatisfaction', 
                        'SpecialProjectsCount', 'Absences', 'Skor_SAW', 'Ranking']], 
             use_container_width=True)

# Visualisasi Top 5
if total_bobot == 1.0:
    st.header("Visualisasi Top 5 Karyawan")
    top5 = df_result.head(5)
    
    # Grafik batang
    fig_bar = px.bar(top5, x='Employee_Name', y='Skor_SAW', 
                     color='Skor_SAW', color_continuous_scale='Blues',
                     title='Top 5 Karyawan Terbaik (Metode SAW)',
                     labels={'Skor_SAW': 'Skor SAW', 'Employee_Name': 'Nama Karyawan'})
    fig_bar.update_layout(xaxis_tickangle=30)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Histogram distribusi skor
    fig_hist = px.histogram(df_result, x='Skor_SAW', nbins=20,
                            title='Distribusi Skor SAW Karyawan',
                            labels={'Skor_SAW': 'Skor SAW'})
    st.plotly_chart(fig_hist, use_container_width=True)

# Ekspor hasil
if total_bobot == 1.0:
    st.header("Ekspor Hasil")
    csv = df_result.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Unduh Hasil Peringkat (CSV)",
        data=csv,
        file_name='ranking_karyawan_saw.csv',
        mime='text/csv'
    )

# Penjelasan metode
with st.expander("Penjelasan Metode SAW"):
    st.markdown("""
    **Simple Additive Weighting (SAW)** adalah metode pengambilan keputusan multi-kriteria yang sederhana dan efektif. Langkah-langkahnya:
    1. **Menentukan Kriteria dan Bobot**: Kriteria seperti Engagement Survey, Employee Satisfaction, dll., diberi bobot sesuai prioritas (jumlah bobot = 1).
    2. **Normalisasi Data**: Nilai setiap kriteria dinormalisasi ke skala 0-1 menggunakan Min-Max Scaling.
    3. **Penghitungan Skor**: Skor akhir dihitung dengan mengalikan nilai normalisasi dengan bobot, lalu menjumlahkannya.
    4. **Peringkat**: Karyawan diurutkan berdasarkan skor tertinggi.
    
    **Catatan**: Kolom Absensi dibalik (nilai kecil lebih baik) sebelum dinormalisasi.
    """)