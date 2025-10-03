# ==================================================
# STREAMLIT - Program Pengurangan & Pengolahan (FIXED UNIQUE COUNTS)
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
    "Maggot/BSF": "#1b7837",
    "Komposting": "#4daf4a",
    "Bank Sampah": "#ffff99",
    "Reduce Plastik": "#b2df8a",
    "Lainnya": "#d9f0a3",
    "Organik": "#238443",
    "Anorganik": "#ffffbf",
    "Plastik": "#addd8e",
    "Campuran": "#f7fcb9"
}

# =============================
# HELPER: DEDUP PROGRAM UNIK
# =============================
UNIQ_KEYS = [c for c in ["perusahaan","site","nama_program","kategori","cluster","jenis_sampah"] if c in df_program.columns]

def unique_program_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ambil 1 baris unik per program (abaikan dimensi bulan_tahun/periode)."""
    d = df.copy()
    if "nama_program" in d.columns:
        d = d.dropna(subset=["nama_program"])
    # Tidak gunakan kolom bulan/periode saat dedup
    return d.drop_duplicates(subset=UNIQ_KEYS)

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
    df_prog_long["periode"] = pd.to_datetime(
        df_prog_long["tahun"].astype(str)+"-"+df_prog_long["bulan"].map(bulan_map).astype(str)+"-01"
    )

    tahun_tersedia = sorted(df_prog_long["tahun"].unique())
    bulan_tersedia = list(bulan_map.keys())
    tahun_pilihan = st.sidebar.multiselect("Pilih Tahun:", tahun_tersedia, default=tahun_tersedia)
    bulan_pilihan = st.sidebar.multiselect("Pilih Bulan:", bulan_tersedia, default=bulan_tersedia)

    df_prog_filtered = df_prog_long[
        (df_prog_long["tahun"].isin(tahun_pilihan)) &
        (df_prog_long["bulan"].isin(bulan_pilihan))
    ].copy()
else:
    df_prog_filtered = df_program.copy()
    tahun_pilihan, bulan_pilihan = [], []
    bulan_map = {}

# Apply filter site & perusahaan
if site_sel and "site" in df_prog_filtered.columns:
    df_prog_filtered = df_prog_filtered[df_prog_filtered["site"].isin(site_sel)]
if perusahaan_sel and "perusahaan" in df_prog_filtered.columns:
    df_prog_filtered = df_prog_filtered[df_prog_filtered["perusahaan"].isin(perusahaan_sel)]

# =============================
# HITUNG JUMLAH HARI
# =============================
days_period = 0
if bulan_tahun_cols and tahun_pilihan and bulan_pilihan:
    for y in tahun_pilihan:
        for b in bulan_pilihan:
            days_period += calendar.monthrange(y, bulan_map[b])[1]
else:
    days_period = 609  # fallback default

st.info(f"📅 Total jumlah hari periode filter: **{days_period} hari**")

# ====== DATA UNIK (SETELAH FILTER) UNTUK SEMUA METRIC JUMLAH PROGRAM ======
df_prog_unique = unique_program_df(df_prog_filtered)

# =============================
# METRICS (FIXED)
# =============================
jumlah_program = df_prog_unique.shape[0]

if "kategori" in df_prog_unique.columns:
    jmlprog_pengurangan = df_prog_unique[df_prog_unique["kategori"]=="Program Pengurangan"].shape[0]
    jmlprog_pengelolaan = df_prog_unique[df_prog_unique["kategori"]=="Program Pengelolaan"].shape[0]
else:
    jmlprog_pengurangan = jmlprog_pengelolaan = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Program", jumlah_program, "per Agustus 2025")
col2.metric("Program Pengurangan", jmlprog_pengurangan, "(Reduce)")
col3.metric("Program Pengelolaan", jmlprog_pengelolaan, "(Reuse & Recycle)")
col4.metric("Periode Hari", f"{days_period} hari")

# =============================
# CLUSTER METRICS (FIXED)
# =============================
col1, col2, col3, col4, col5 = st.columns(5)
for i, cluster in enumerate(["Maggot/BSF","Komposting","Bank Sampah","Reduce Plastik","Lainnya"]):
    col = [col1,col2,col3,col4,col5][i]
    if "cluster" in df_prog_unique.columns:
        col.metric(cluster, df_prog_unique[df_prog_unique["cluster"]==cluster].shape[0])
    else:
        col.metric(cluster, 0)

# =============================
# VISUALISASI
# =============================

# Sunburst (pakai program unik agar tidak double-count)
st.markdown("### 📊 Proporsi Program & Jenis Sampah")
if not df_prog_unique.empty and {"cluster","jenis_sampah"}.issubset(df_prog_unique.columns):
    df_sun = df_prog_unique.groupby(["cluster","jenis_sampah"], as_index=False).size()
    df_sun.rename(columns={"size":"jumlah_program"}, inplace=True)
    fig_sunburst = px.sunburst(
        df_sun, path=["cluster","jenis_sampah"], values="jumlah_program",
        color="cluster", color_discrete_map=color_map
    )
    st.plotly_chart(fig_sunburst, use_container_width=True)

# Pie (kategori & jenis sampah) – juga pakai data unik
st.markdown("### 🥧 Proporsi Program (Kategori & Jenis Sampah)")
if not df_prog_unique.empty and {"kategori","jenis_sampah"}.issubset(df_prog_unique.columns):
    df_prop = df_prog_unique.groupby(["kategori","jenis_sampah"], as_index=False).size()
    df_prop.rename(columns={"size":"jumlah_program"}, inplace=True)
    fig_prop = px.pie(
        df_prop, values="jumlah_program", names="jenis_sampah",
        color="jenis_sampah", color_discrete_map=color_map, hole=0.3
    )
    st.plotly_chart(fig_prop, use_container_width=True)

# Line Trend Cluster – tetap pakai nilai bulanan (value)
st.markdown("### 📈 Tren Sampah per Cluster")
if "periode" in df_prog_filtered.columns and "value" in df_prog_filtered.columns and "cluster" in df_prog_filtered.columns:
    trend_cluster = df_prog_filtered.groupby(["periode","cluster"], as_index=False)["value"].sum()
    fig_line = px.line(trend_cluster, x="periode", y="value", color="cluster", markers=True,
                       color_discrete_map=color_map)
    st.plotly_chart(fig_line, use_container_width=True)

# Sankey – gunakan jumlah program unik (bukan baris bulanan)
st.markdown("### 🔗 Sankey Diagram: Timbulan → Cluster")
if not df_prog_unique.empty and {"jenis_sampah","cluster"}.issubset(df_prog_unique.columns):
    df_sankey = df_prog_unique.groupby(["jenis_sampah","cluster"], as_index=False).size()
    df_sankey.rename(columns={"size":"jumlah_program"}, inplace=True)
    sources = list(df_sankey["jenis_sampah"].unique()) + list(df_sankey["cluster"].unique())
    mapping = {name:i for i,name in enumerate(sources)}
    link = {
        "source":[mapping[s] for s in df_sankey["jenis_sampah"]],
        "target":[mapping[t] for t in df_sankey["cluster"]],
        "value":df_sankey["jumlah_program"]
    }
    node = {
        "label":sources, "pad":20, "thickness":20,
        "color":[color_map.get(l,"#66c2a5") for l in sources]
    }
    fig_sankey = go.Figure(go.Sankey(node=node, link=link))
    st.plotly_chart(fig_sankey, use_container_width=True)

# Bar Distribusi Cluster – hitung jumlah program unik per perusahaan-site-cluster
st.markdown("### 🏢 Distribusi Cluster Program per Perusahaan & Site")
if not df_prog_unique.empty and {"perusahaan","site","cluster","nama_program"}.issubset(df_prog_unique.columns):
    df_dist = (df_prog_unique
               .groupby(["perusahaan","site","cluster"])["nama_program"]
               .nunique()
               .reset_index(name="jumlah_program"))
    fig_bar = px.bar(
        df_dist, x="perusahaan", y="jumlah_program", color="cluster", facet_col="site",
        barmode="stack", text="jumlah_program", color_discrete_map=color_map
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Line Trend Kategori – tetap pakai nilai bulanan (value)
st.markdown("### 📈 Tren Sampah Terkelola & Ter Kurangi (Kategori)")
if {"periode","kategori","value"}.issubset(df_prog_filtered.columns):
    trend_kat = df_prog_filtered.groupby(["periode","kategori"], as_index=False)["value"].sum()
    fig_trend = px.line(trend_kat, x="periode", y="value", color="kategori", markers=True,
                        color_discrete_map=color_map)
    st.plotly_chart(fig_trend, use_container_width=True)

# Bar Timbulan vs Terkelola vs Reduce – per perusahaan-site (pakai value sum)
st.markdown("### 🏢 Timbulan vs Terkelola vs Reduce (Perusahaan-Site)")
if not df_timbulan.empty and "timbulan" in df_timbulan.columns:
    df_timbulan["timbulan"] = pd.to_numeric(df_timbulan["timbulan"], errors="coerce")
    df_pengelolaan = df_prog_filtered[df_prog_filtered.get("kategori","")=="Program Pengelolaan"].copy()
    df_pengurangan = df_prog_filtered[df_prog_filtered.get("kategori","")=="Program Pengurangan"].copy()
    df_merge = df_timbulan.groupby(["perusahaan","site"], as_index=False)["timbulan"].sum()

    if not df_pengelolaan.empty and "value" in df_pengelolaan.columns:
        df_merge = df_merge.merge(
            df_pengelolaan.groupby(["perusahaan","site"], as_index=False)["value"].sum()
                          .rename(columns={"value":"terkelola"}),
            on=["perusahaan","site"], how="left"
        )
    if not df_pengurangan.empty and "value" in df_pengurangan.columns:
        df_merge = df_merge.merge(
            df_pengurangan.groupby(["perusahaan","site"], as_index=False)["value"].sum()
                          .rename(columns={"value":"reduce"}),
            on=["perusahaan","site"], how="left"
        )
    df_merge[["terkelola","reduce"]] = df_merge[["terkelola","reduce"]].fillna(0)
    df_merge["tidak_terkelola"] = df_merge["timbulan"] - df_merge["terkelola"]

    fig_bar2 = go.Figure()
    xlab = df_merge["perusahaan"]+" - "+df_merge["site"]
    fig_bar2.add_bar(x=xlab, y=df_merge["timbulan"], name="Timbulan", marker_color="#ffff99")
    fig_bar2.add_bar(x=xlab, y=df_merge["terkelola"], name="Terkelola", marker_color="#1b7837")
    fig_bar2.add_bar(x=xlab, y=df_merge["tidak_terkelola"], name="Tidak Terkelola", marker_color="#b2df8a")
    fig_bar2.add_bar(x=xlab, y=df_merge["reduce"], name="Reduce", marker_color="#4daf4a")
    fig_bar2.update_layout(barmode="group", xaxis_tickangle=-45)
    st.plotly_chart(fig_bar2, use_container_width=True)

# =============================
# INSIGHT (pakai data unik)
# =============================
st.markdown("### 📌 Insight Otomatis")
if not df_prog_unique.empty and "cluster" in df_prog_unique.columns:
    df_dist_u = df_prog_unique.groupby(["perusahaan","site","cluster"], as_index=False).size()
    top_cluster = df_dist_u.groupby("cluster")["size"].sum().idxmax()
    top_company = df_dist_u.groupby("perusahaan")["size"].sum().idxmax()
    top_site = df_dist_u.groupby("site")["size"].sum().idxmax()
    st.info(f"📍 Program dominan: **{top_cluster}** | Perusahaan terbanyak: **{top_company}** | Site paling aktif: **{top_site}**")
else:
    st.warning("Tidak ada data yang sesuai dengan filter.")
