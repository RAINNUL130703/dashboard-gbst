# pages/4_Ketidaksesuaian.py
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# ===============================
# LOGO + HEADER
# ===============================
logo = "assets/4logo.png"
st.logo(logo, icon_image=logo, size="large")

st.markdown(
    """
    <h1 style="font-size:24px; color:#000000; font-weight:bold; margin-bottom:0.5px;">
    📝 Ketidaksesuaian Pengelolaan Sampah
    </h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# LOAD DATA GOOGLE SHEETS
# ===============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.lower()
    )
    return df

if "data" not in st.session_state:
    sheet_names = ["Ketidaksesuaian", "Survei_Online", "Survei_Offline"]
    data_dict = {}
    for sheet in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
            df = pd.read_csv(url)
            df = norm_cols(df)
            data_dict[sheet] = df
        except Exception as e:
            st.error(f"Gagal load sheet {sheet}: {e}")
            data_dict[sheet] = pd.DataFrame()
    st.session_state["data"] = data_dict

df = st.session_state["data"].get("Ketidaksesuaian", pd.DataFrame())
df_online = st.session_state["data"].get("Survei_Online", pd.DataFrame())
df_offline = st.session_state["data"].get("Survei_Offline", pd.DataFrame())
df_survey = pd.concat([df_online, df_offline], ignore_index=True)

if df.empty:
    st.warning("❌ Data `Ketidaksesuaian` tidak ditemukan.")
    st.stop()

# ===============================
# NORMALISASI KOLOM KETIDAKSESUAIAN
# ===============================
df["status_temuan"] = df["status_temuan"].astype(str).str.strip().str.title()

if "kategori_subketidaksesuaian" in df.columns:
    df["kategori_subketidaksesuaian"] = (
        df["kategori_subketidaksesuaian"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.title()
    )

# ===============================
# METRICS
# ===============================
total_reports = len(df)
df_valid = df[df["status_temuan"] == "Valid"].copy()
total_valid = len(df_valid)
pct_valid = (total_valid / total_reports * 100) if total_reports > 0 else 0

count_perilaku = (df_valid["kategori_subketidaksesuaian"] == "Perilaku").sum()
count_nonperilaku = (df_valid["kategori_subketidaksesuaian"] == "Non Perilaku").sum()

pct_perilaku = (count_perilaku / total_valid * 100) if total_valid > 0 else 0
pct_nonperilaku = (count_nonperilaku / total_valid * 100) if total_valid > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Jumlah Laporan", total_reports)
with col2:
    st.metric("Laporan Valid", total_valid, f"{pct_valid:.1f}% dari total")
with col3:
    st.metric("Kategori Perilaku", count_perilaku, f"{pct_perilaku:.1f}% dari valid")
with col4:
    st.metric("Kategori Non Perilaku", count_nonperilaku, f"{pct_nonperilaku:.1f}% dari valid")

st.markdown("---")

# ===============================
# TREN WAKTU
# ===============================
st.subheader("📈 Tren: Perilaku vs Non-Perilaku (Valid)")
if "tanggallapor" in df_valid.columns:
    df_valid["tanggallapor"] = pd.to_datetime(df_valid["tanggallapor"], errors="coerce")
    df_valid["period_month"] = df_valid["tanggallapor"].dt.to_period("M")
    trend = df_valid.groupby(["period_month", "kategori_subketidaksesuaian"]).size().reset_index(name="count")
    if not trend.empty:
        pivot = trend.pivot(index="period_month", columns="kategori_subketidaksesuaian", values="count").fillna(0)
        pivot.index = pivot.index.to_timestamp()
        fig = go.Figure()
        for col in pivot.columns:
            fig.add_trace(go.Scatter(x=pivot.index, y=pivot[col], mode="lines+markers", name=col))
        fig.update_layout(height=350, xaxis_title="Bulan", yaxis_title="Jumlah Laporan (Valid)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data tanggal valid untuk tren.")
else:
    st.warning("Kolom 'tanggallapor' tidak ditemukan.")

st.markdown("---")

# ===============================
# PROPORSI SUB-KETIDAKSESUAIAN
# ===============================
st.subheader("📊 Proporsi berdasarkan Sub-Ketidaksesuaian (Valid)")
if "sub_ketidaksesuaian" in df_valid.columns:
    sub_counts = df_valid["sub_ketidaksesuaian"].value_counts().reset_index()
    sub_counts.columns = ["Sub Ketidaksesuaian", "Jumlah"]
    fig = px.sunburst(
        sub_counts,
        path=["Sub Ketidaksesuaian"],
        values="Jumlah",
        color="Jumlah",
        color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Kolom 'sub_ketidaksesuaian' tidak ditemukan.")

st.markdown("---")

# ===============================
# JUMLAH PER SITE
# ===============================
st.subheader("🔍 Jumlah Sub-Ketidaksesuaian per Site - Perusahaan (Valid)")
if "perusahaan" in df_valid.columns and "site" in df_valid.columns and "sub_ketidaksesuaian" in df_valid.columns:
    df_valid["company_site"] = df_valid["perusahaan"].astype(str).str.strip() + " - " + df_valid["site"].astype(str).str.strip()
    grp = df_valid.groupby(["company_site", "sub_ketidaksesuaian"]).size().reset_index(name="count")
    pivot_cs = grp.pivot(index="company_site", columns="sub_ketidaksesuaian", values="count").fillna(0)

    fig = go.Figure()
    for col in pivot_cs.columns:
        fig.add_trace(go.Bar(y=pivot_cs.index, x=pivot_cs[col], name=col, orientation="h"))
    fig.update_layout(barmode="stack", height=600, xaxis_title="Jumlah Temuan (Valid)", yaxis_title="Perusahaan - Site")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(grp)
else:
    st.warning("Kolom perusahaan/site/sub_ketidaksesuaian tidak ditemukan.")

st.markdown("---")

# ===============================
# TOP 3 SITE
# ===============================
st.subheader("🏆 Top 3 Site dengan Ketidaksesuaian Valid")
if "perusahaan" in df_valid.columns and "site" in df_valid.columns:
    top3 = df_valid.groupby(["perusahaan", "site"]).size().reset_index(name="count").sort_values("count", ascending=False).head(3)
    for _, row in top3.iterrows():
        st.markdown(f"**{row['count']}** — {row['perusahaan']} · {row['site']}")
    st.dataframe(top3)
else:
    st.warning("Kolom perusahaan/site tidak ditemukan.")

st.markdown("---")

# ===============================
# ===============================
# ANALISIS KORELASI FEEDBACK Q2
# ===============================
st.header("📈 Analisis Korelasi: Feedback Q2 vs Ketidaksesuaian")

col_site = "site___lokasi_kerja"
col_corp = "perusahaan_area_kerja_tambang"
col_q2 = "2._seberapa_optimal_program_gbst_berjalan_selama_ini_di_perusahaan_anda?"

if not df_survey.empty and not df.empty:
    if col_site in df_survey.columns and col_corp in df_survey.columns and col_q2 in df_survey.columns:
        df_survey[col_q2] = pd.to_numeric(df_survey[col_q2], errors="coerce")
        df_feedback = (
            df_survey.groupby([col_corp, col_site])[col_q2]
            .mean().reset_index()
            .rename(columns={col_corp:"perusahaan", col_site:"site", col_q2:"feedback_q2"})
        )

        # Hitung total ketidaksesuaian valid
        df_valid = df[df["status_temuan"] == "Valid"].copy()
        df_count = df_valid.groupby(["perusahaan","site"]).size().reset_index(name="jumlah_ketidaksesuaian")

        # Hitung perilaku & non-perilaku
        perilaku_count = df_valid[df_valid["kategori_subketidaksesuaian"]=="Perilaku"].groupby(
            ["perusahaan","site"]).size().reset_index(name="jumlah_perilaku")
        nonperilaku_count = df_valid[df_valid["kategori_subketidaksesuaian"]=="Non Perilaku"].groupby(
            ["perusahaan","site"]).size().reset_index(name="jumlah_nonperilaku")

        # Merge semua
        df_corr = pd.merge(df_feedback, df_count, on=["perusahaan","site"], how="left")
        df_corr = pd.merge(df_corr, perilaku_count, on=["perusahaan","site"], how="left")
        df_corr = pd.merge(df_corr, nonperilaku_count, on=["perusahaan","site"], how="left")
        df_corr = df_corr.fillna(0)

        # Normalisasi ke skala 0–5
        scaler = MinMaxScaler(feature_range=(0,5))
        df_corr[["ketidaksesuaian_scaled","perilaku_scaled","nonperilaku_scaled"]] = scaler.fit_transform(
            df_corr[["jumlah_ketidaksesuaian","jumlah_perilaku","jumlah_nonperilaku"]])

        # Korelasi
        corr_val = df_corr["feedback_q2"].corr(df_corr["jumlah_ketidaksesuaian"])

        # Baseline rata-rata feedback
        baseline_opt = df_corr["feedback_q2"].mean()


        # FILTER
        perusahaan_opts = ["Semua"] + sorted(df_corr["perusahaan"].unique().tolist())
        pilih_perusahaan = st.selectbox("Pilih Perusahaan", perusahaan_opts)

        site_opts = ["Semua"] + sorted(df_corr["site"].unique().tolist())
        pilih_site = st.selectbox("Pilih Site", site_opts)

        df_filtered = df_corr.copy()
        if pilih_perusahaan != "Semua":
            df_filtered = df_filtered[df_filtered["perusahaan"]==pilih_perusahaan]
        if pilih_site != "Semua":
            df_filtered = df_filtered[df_filtered["site"]==pilih_site]

        # Company-Site gabungan
        df_corr["company_site"] = df_corr["perusahaan"] + " - " + df_corr["site"]

        # ============== VISUALISASI ==============
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_corr["company_site"], y=df_corr["feedback_q2"],
                                 mode="lines+markers", name="Feedback Q2 (1-5)", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=df_corr["company_site"], y=df_corr["ketidaksesuaian_scaled"],
                                 mode="lines+markers", name="Ketidaksesuaian (scaled 0-5)", line=dict(color="red")))
        fig.add_trace(go.Scatter(x=df_corr["company_site"], y=df_corr["perilaku_scaled"],
                                 mode="lines+markers", name="Perilaku (scaled 0-5)", line=dict(color="orange", dash="dot")))
        fig.add_trace(go.Scatter(x=df_corr["company_site"], y=df_corr["nonperilaku_scaled"],
                                 mode="lines+markers", name="Non-Perilaku (scaled 0-5)", line=dict(color="green", dash="dot")))

        # baseline garis rata-rata feedback
        fig.add_hline(y=baseline_opt, line_dash="dot", line_color="green",
                      annotation_text=f"Baseline rata-rata Feedback = {baseline_opt:.1f}",
                      annotation_position="bottom right")

        fig.update_layout(
            title=f"Korelasi Feedback vs Ketidaksesuaian (r={corr_val:.2f})",
            xaxis_title="Perusahaan - Site",
            yaxis_title="Skala (0–5)",
            height=600,
            legend=dict(x=0, y=-0.25, orientation="h")  # pindahkan legend bawah
        )


        st.plotly_chart(fig, use_container_width=True)

        # tampilkan dataframe
        st.subheader("📋 Dataframe dengan Skala")
        st.dataframe(df_corr[[
            "perusahaan","site","feedback_q2","jumlah_ketidaksesuaian",
            "jumlah_perilaku","jumlah_nonperilaku",
            "ketidaksesuaian_scaled","perilaku_scaled","nonperilaku_scaled"
        ]])
    else:
        st.warning("Kolom Q2 atau identitas site/perusahaan tidak ditemukan di survei.")
else:
    st.warning("❌ Data survei atau ketidaksesuaian kosong.")

st.markdown("---")

# ===============================
# EKSPOR DATA
# ===============================
st.subheader("📥 Ekspor Data (opsional)")
if not df_valid.empty:
    csv = df_valid.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV Laporan Valid", data=csv, file_name="ketidaksesuaian_valid.csv", mime="text/csv")
else:
    st.info("Tidak ada laporan valid untuk diunduh.")
