# ==================================================
# STREAMLIT - Program Pengurangan & Pengolahan (FINAL ECO THEME)
# ==================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar, re

st.markdown('<p style="text-align: left;font-weight: bold;">♻️ Program Pengurangan & Pengolahan</p>', unsafe_allow_html=True)

# =============================
# LOAD DATA GOOGLE SHEETS
# =============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
sheet_name = ["Timbulan","Program","Survei_Online","Ketidaksesuaian","Survei_Offline","CCTV","Koordinat_UTM"]

all_df = {}
for sheet in sheet_name:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")

# =============================
# AMBIL DATAFRAME
# =============================
df_timbulan = all_df.get("Timbulan", pd.DataFrame()).copy()
df_program = all_df.get("Program", pd.DataFrame()).copy()
df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame()).copy()

# =============================
# NORMALISASI NAMA KOLOM
# =============================
def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return df

df_timbulan = norm_cols(df_timbulan)
df_program = norm_cols(df_program)
df_ketidaksesuaian = norm_cols(df_ketidaksesuaian)

# =============================
# NORMALISASI NAMA PROGRAM
# =============================
def normalize_name(text: str):
    if pd.isna(text): return ""
    txt = str(text).lower()
    txt = txt.replace("magot", "maggot").replace("vermikomposting", "komposting")
    txt = txt.replace("meal box", "mealbox").replace("pack meal", "packmeal")
    return txt.title()

if "nama_program" in df_program.columns:
    df_program["nama_program"] = df_program["nama_program"].map(normalize_name)

# =============================
# CLUSTER PROGRAM
# =============================
def cluster_program(name: str):
    txt = str(name).lower()
    if re.search(r"maggot|hermetia|larva|budidaya", txt): return "Maggot/BSF"
    if re.search(r"kompos|komposting|vermi", txt): return "Komposting"
    if "bank sampah" in txt: return "Bank Sampah"
    if re.search(r"reduce|tumbler|mealbox|packmeal|diet plastik|prasmanan", txt): return "Reduce Plastik"
    return "Lainnya"

df_program["cluster"] = df_program["nama_program"].map(cluster_program)

def map_timbulan(cluster):
    if cluster in ["Maggot/BSF","Komposting"]: return "Organik"
    if cluster == "Bank Sampah": return "Anorganik"
    if cluster == "Reduce Plastik": return "Plastik"
    return "Campuran"

df_program["jenis_sampah"] = df_program["cluster"].map(map_timbulan)

# =============================
# PALET WARNA ECO
# =============================
color_map = {
    "Maggot/BSF": "#1b7837",       # hijau tua
    "Komposting": "#4daf4a",      # hijau medium
    "Bank Sampah": "#ffff99",     # kuning muda
    "Reduce Plastik": "#b2df8a",  # hijau muda
    "Lainnya": "#d9f0a3",         # hijau lemon
    "Organik": "#238443",
    "Anorganik": "#ffffbf",
    "Plastik": "#addd8e",
    "Campuran": "#f7fcb9"
}

# =============================
# FILTER SIDEBAR
# =============================
st.sidebar.subheader("Filter Data")

site_list = sorted(df_program["site"].dropna().unique()) if "site" in df_program.columns else []
site_sel = st.sidebar.multiselect("Pilih Site", site_list, default=site_list)

perusahaan_list = sorted(df_program["perusahaan"].dropna().unique()) if "perusahaan" in df_program.columns else []
perusahaan_sel = st.sidebar.multiselect("Pilih Perusahaan", perusahaan_list, default=perusahaan_list)

# Filter Tahun & Bulan
pattern = r"^(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)_\d{4}$"
bulan_tahun_cols = [col for col in df_program.columns if re.match(pattern, str(col))]

if bulan_tahun_cols:
    df_prog_long = df_program.melt(
        id_vars=[col for col in df_program.columns if col not in bulan_tahun_cols],
        value_vars=bulan_tahun_cols,
        var_name="bulan_tahun",
        value_name="value"
    )
    df_prog_long["tahun"] = df_prog_long["bulan_tahun"].apply(lambda x: int(x.split("_")[1]))
    df_prog_long["bulan"] = df_prog_long["bulan_tahun"].apply(lambda x: x.split("_")[0].capitalize())
    bulan_map = {"Januari":1,"Februari":2,"Maret":3,"April":4,"Mei":5,"Juni":6,
                 "Juli":7,"Agustus":8,"September":9,"Oktober":10,"November":11,"Desember":12}
    df_prog_long["periode"] = pd.to_datetime(df_prog_long["tahun"].astype(str)+"-"+df_prog_long["bulan"].map(bulan_map).astype(str)+"-01")

    tahun_tersedia = sorted(df_prog_long["tahun"].unique())
    bulan_tersedia = list(bulan_map.keys())
    tahun_pilihan = st.sidebar.multiselect("Pilih Tahun:", tahun_tersedia, default=tahun_tersedia)
    bulan_pilihan = st.sidebar.multiselect("Pilih Bulan:", bulan_tersedia, default=bulan_tersedia)

    df_prog_filtered = df_prog_long[
        (df_prog_long["tahun"].isin(tahun_pilihan)) & 
        (df_prog_long["bulan"].isin(bulan_pilihan))
    ]
else:
    df_prog_filtered = df_program.copy()

# Apply filter site & perusahaan
if site_sel:
    df_prog_filtered = df_prog_filtered[df_prog_filtered["site"].isin(site_sel)]
if perusahaan_sel:
    df_prog_filtered = df_prog_filtered[df_prog_filtered["perusahaan"].isin(perusahaan_sel)]

# =============================
# HITUNG JUMLAH HARI
# =============================
days_period = 0
if bulan_tahun_cols:
    for y in tahun_pilihan:
        for b in bulan_pilihan:
            days_period += calendar.monthrange(y, bulan_map[b])[1]
else:
    days_period = 609  # default

st.info(f"📅 Total jumlah hari periode filter: **{days_period} hari**")

# =============================
# METRICS
# =============================
jumlah_program = df_prog_filtered["nama_program"].dropna().shape[0] if "nama_program" in df_prog_filtered.columns else 0
jmlprog_pengurangan = df_prog_filtered[df_prog_filtered["kategori"]=="Program Pengurangan"]["nama_program"].nunique() if "kategori" in df_prog_filtered.columns else 0
jmlprog_pengelolaan = df_prog_filtered[df_prog_filtered["kategori"]=="Program Pengelolaan"]["nama_program"].nunique() if "kategori" in df_prog_filtered.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Program", jumlah_program, "per Agustus 2025")
col2.metric("Program Pengurangan", jmlprog_pengurangan, "(Reduce)")
col3.metric("Program Pengelolaan", jmlprog_pengelolaan, "(Reuse & Recycle)")
col4.metric("Periode Hari", f"{days_period} hari")

# =============================
# CLUSTER METRICS
# =============================
col1, col2, col3, col4, col5 = st.columns(5)
for i, cluster in enumerate(["Maggot/BSF","Komposting","Bank Sampah","Reduce Plastik","Lainnya"]):
    col = [col1,col2,col3,col4,col5][i]
    col.metric(cluster, df_prog_filtered[df_prog_filtered["cluster"]==cluster]["nama_program"].nunique() if "cluster" in df_prog_filtered.columns else 0)

# =============================
# VISUALISASI
# =============================

# Sunburst
st.markdown("### 📊 Proporsi Program & Jenis Sampah")
if not df_prog_filtered.empty and "cluster" in df_prog_filtered.columns:
    df_sun = df_prog_filtered.groupby(["cluster","jenis_sampah"])["nama_program"].count().reset_index()
    fig_sunburst = px.sunburst(df_sun, path=["cluster","jenis_sampah"], values="nama_program",
                               color="cluster", color_discrete_map=color_map)
    st.plotly_chart(fig_sunburst, use_container_width=True)

# Pie (kategori & jenis sampah)
st.markdown("### 🥧 Proporsi Program (Kategori & Jenis Sampah)")
if not df_prog_filtered.empty and "kategori" in df_prog_filtered.columns:
    df_prop = df_prog_filtered.groupby(["kategori","jenis_sampah"])["nama_program"].count().reset_index()
    fig_prop = px.pie(df_prop, values="nama_program", names="jenis_sampah", color="jenis_sampah",
                      color_discrete_map=color_map, hole=0.3)
    st.plotly_chart(fig_prop, use_container_width=True)

# Line Trend Cluster
st.markdown("### 📈 Tren Sampah per Cluster")
if "bulan_tahun" in df_prog_filtered.columns:
    trend_cluster = df_prog_filtered.groupby(["periode","cluster"])["value"].sum().reset_index()
    fig_line = px.line(trend_cluster, x="periode", y="value", color="cluster", markers=True,
                       color_discrete_map=color_map)
    st.plotly_chart(fig_line, use_container_width=True)

# Sankey
st.markdown("### 🔗 Sankey Diagram: Timbulan → Cluster")
if not df_prog_filtered.empty and "cluster" in df_prog_filtered.columns:
    df_sankey = df_prog_filtered.groupby(["jenis_sampah","cluster"])["nama_program"].count().reset_index()
    sources = list(df_sankey["jenis_sampah"].unique()) + list(df_sankey["cluster"].unique())
    mapping = {name:i for i,name in enumerate(sources)}
    link = {"source":[mapping[s] for s in df_sankey["jenis_sampah"]],
            "target":[mapping[t] for t in df_sankey["cluster"]],
            "value":df_sankey["nama_program"]}
    node = {"label":sources, "pad":20, "thickness":20,
            "color":[color_map.get(l,"#66c2a5") for l in sources]}
    fig_sankey = go.Figure(go.Sankey(node=node, link=link))
    st.plotly_chart(fig_sankey, use_container_width=True)

# Bar Distribusi Cluster
st.markdown("### 🏢 Distribusi Cluster Program per Perusahaan & Site")
if not df_prog_filtered.empty and "cluster" in df_prog_filtered.columns:
    df_dist = df_prog_filtered.groupby(["perusahaan","site","cluster"])["nama_program"].count().reset_index()
    fig_bar = px.bar(df_dist, x="perusahaan", y="nama_program", color="cluster", facet_col="site",
                     barmode="stack", text="nama_program", color_discrete_map=color_map)
    st.plotly_chart(fig_bar, use_container_width=True)

# Line Trend Kategori (Reduce vs Pengelolaan)
st.markdown("### 📈 Tren Sampah Terkelola & Ter Kurangi (Kategori)")
if "bulan_tahun" in df_prog_filtered.columns and "kategori" in df_prog_filtered.columns:
    trend_kat = df_prog_filtered.groupby(["periode","kategori"])["value"].sum().reset_index()
    fig_trend = px.line(trend_kat, x="periode", y="value", color="kategori", markers=True,
                        color_discrete_map=color_map)
    st.plotly_chart(fig_trend, use_container_width=True)

# Bar Timbulan vs Terkelola vs Reduce
st.markdown("### 🏢 Timbulan vs Terkelola vs Reduce (Perusahaan-Site)")
if not df_timbulan.empty and "timbulan" in df_timbulan.columns:
    df_timbulan["timbulan"] = pd.to_numeric(df_timbulan["timbulan"], errors="coerce")
    df_pengelolaan = df_prog_filtered[df_prog_filtered["kategori"]=="Program Pengelolaan"].copy()
    df_pengurangan = df_prog_filtered[df_prog_filtered["kategori"]=="Program Pengurangan"].copy()
    df_merge = df_timbulan.groupby(["perusahaan","site"])["timbulan"].sum().reset_index()
    if not df_pengelolaan.empty and "value" in df_pengelolaan.columns:
        df_merge = df_merge.merge(df_pengelolaan.groupby(["perusahaan","site"])["value"].sum().reset_index().rename(columns={"value":"terkelola"}), on=["perusahaan","site"], how="left")
    if not df_pengurangan.empty and "value" in df_pengurangan.columns:
        df_merge = df_merge.merge(df_pengurangan.groupby(["perusahaan","site"])["value"].sum().reset_index().rename(columns={"value":"reduce"}), on=["perusahaan","site"], how="left")
    df_merge.fillna(0,inplace=True)
    df_merge["tidak_terkelola"] = df_merge["timbulan"] - df_merge["terkelola"]

    fig_bar2 = go.Figure()
    fig_bar2.add_bar(x=df_merge["perusahaan"]+" - "+df_merge["site"], y=df_merge["timbulan"], name="Timbulan", marker_color="#ffff99")
    fig_bar2.add_bar(x=df_merge["perusahaan"]+" - "+df_merge["site"], y=df_merge["terkelola"], name="Terkelola", marker_color="#1b7837")
    fig_bar2.add_bar(x=df_merge["perusahaan"]+" - "+df_merge["site"], y=df_merge["tidak_terkelola"], name="Tidak Terkelola", marker_color="#b2df8a")
    fig_bar2.add_bar(x=df_merge["perusahaan"]+" - "+df_merge["site"], y=df_merge["reduce"], name="Reduce", marker_color="#4daf4a")
    fig_bar2.update_layout(barmode="group", xaxis_tickangle=-45)
    st.plotly_chart(fig_bar2, use_container_width=True)

# =============================
# INSIGHT
# =============================
st.markdown("### 📌 Insight Otomatis")
if not df_prog_filtered.empty and "cluster" in df_prog_filtered.columns:
    df_dist = df_prog_filtered.groupby(["perusahaan","site","cluster"])["nama_program"].count().reset_index()
    top_cluster = df_dist.groupby("cluster")["nama_program"].sum().idxmax()
    top_company = df_dist.groupby("perusahaan")["nama_program"].sum().idxmax()
    top_site = df_dist.groupby("site")["nama_program"].sum().idxmax()
    st.info(f"📍 Program dominan: **{top_cluster}** | Perusahaan terbanyak: **{top_company}** | Site paling aktif: **{top_site}**")
else:
    st.warning("Tidak ada data yang sesuai dengan filter.")
