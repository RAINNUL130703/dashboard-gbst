import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyproj import Transformer
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import math

# ===============================
# CONFIG DASHBOARD
# ===============================
st.set_page_config(
    page_title="Dashboard GBST",
    page_icon="🌍",
    layout="wide"
)

# ===============================
# LOGO + HEADER
# ===============================
logo = "assets/4logo.png"
st.logo(logo, icon_image=logo, size="large")

st.markdown(
    """
    <h1 style="font-size:24px; color:#000000; font-weight:bold; margin-bottom:0.5px;">
    📈 Dashboard Gerakan Buang Sampah Terpilah (GBST)
    </h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# UTILITIES
# ===============================
def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return df

def company_to_code(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.upper()
         .str.replace(r"[^A-Z ]", "", regex=True)
         .str.split()
         .apply(lambda t: t[-1] if len(t) else "")
    )

# ===============================
# PARSER KOORDINAT (UTM -> WGS84)
# ===============================
transformer = Transformer.from_crs("EPSG:32650", "EPSG:4326", always_xy=True)

def parse_coord(easting, northing):
    try:
        e = float(str(easting).replace("°E","").replace("E","").strip())
        n = float(str(northing).replace("°N","").replace("N","").strip())
    except:
        return None, None

    # Kasus 1: decimal degrees
    if e <= 180 and n <= 90:
        return e, n   # lon, lat

    # Kasus 2: UTM
    if e > 100000 and n > 100000:
        lon, lat = transformer.transform(e, n)
        return lon, lat

    return None, None

# ===============================
# LOAD DATA GOOGLE SHEETS
# ===============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
sheet_names = ["Timbulan", "Program", "Ketidaksesuaian", "Survei_Online", "Survei_Offline", "CCTV", "Koordinat_UTM"]

all_df = {}
for sheet in sheet_names:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")
        all_df[sheet] = pd.DataFrame()

# Dataset (dinormalisasi kolomnya)
df_timbulan = norm_cols(all_df.get("Timbulan", pd.DataFrame()).copy())
df_program = norm_cols(all_df.get("Program", pd.DataFrame()).copy())
df_ketidaksesuaian = norm_cols(all_df.get("Ketidaksesuaian", pd.DataFrame()).copy())
df_online = norm_cols(all_df.get("Survei_Online", pd.DataFrame()).copy())
df_offline = norm_cols(all_df.get("Survei_Offline", pd.DataFrame()).copy())
df_cctv = norm_cols(all_df.get("CCTV", pd.DataFrame()).copy())
df_koordinat = norm_cols(all_df.get("Koordinat_UTM", pd.DataFrame()).copy())


# ===============================
# SIMPAN SEMUA DATA KE SESSION_STATE
# ===============================
st.session_state["data"] = {
    "Timbulan": df_timbulan,
    "Program": df_program,
    "Ketidaksesuaian": df_ketidaksesuaian,
    "Survei_Online": df_online,
    "Survei_Offline": df_offline,
    "CCTV": df_cctv,
    "Koordinat_UTM": df_koordinat
}

# ===============================
# DYNAMIC DAYS PERIOD
# ===============================
if not df_program.empty and "tanggal" in df_program.columns:
    df_program["tanggal"] = pd.to_datetime(df_program["tanggal"], errors="coerce")
    start_date = df_program["tanggal"].min()
    end_date = df_program["tanggal"].max()
    days_period = (end_date - start_date).days if pd.notnull(start_date) and pd.notnull(end_date) else 609
else:
    days_period = 609

# ===============================
# PETA COLOR LIST
# ===============================
COLOR_LIST = [
    "red", "blue", "green", "purple", "orange",
    "darkred", "lightred", "beige", "darkblue", "darkgreen",
    "cadetblue", "darkpurple", "white", "pink", "lightblue",
    "lightgreen", "gray", "black", "lightgray"
]

def assign_color(value, unique_values):
    idx = unique_values.index(value) % len(COLOR_LIST)
    return COLOR_LIST[idx]

# ===============================
# TAB
# ===============================
tab1, tab2 = st.tabs(["Overview", "Data Quality Check"])

with tab1:
    try:
        # ---------- METRIC DASAR ----------
        if "timbulan" in df_timbulan.columns:
            df_timbulan["timbulan"] = pd.to_numeric(
                df_timbulan["timbulan"].astype(str).str.replace(",", "."),
                errors="coerce"
            )
            total_timbulan = df_timbulan["timbulan"].sum()
            total_timbulan_all = pd.to_numeric(
                df_timbulan.get("data_input_total", 0), errors="coerce"
            ).sum()
        else:
            total_timbulan = total_timbulan_all = 0

        if "nama_program" in df_program.columns:
            jumlah_program = df_program["nama_program"].dropna().shape[0]
        else:
            jumlah_program = 0

        if "status_temuan" in df_ketidaksesuaian.columns:
            total_ketidaksesuaian = df_ketidaksesuaian.query("status_temuan == 'valid' or status_temuan == 'Valid'").shape[0]
            temuan_masuk = df_ketidaksesuaian["status_temuan"].count()
        else:
            total_ketidaksesuaian, temuan_masuk = 0, 0

        # ---------- METRIC ----------
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Timbulan (kg)", f"{total_timbulan_all:,.0f}")
        with col2:
            st.metric("Rata-rata Timbulan (kg/hari)", f"{total_timbulan:.2f}")
        with col3:
            st.metric("Jumlah Program", jumlah_program)
        with col4:
            st.metric("Ketidaksesuaian Valid", f"{total_ketidaksesuaian} / {temuan_masuk}")

        # =====================================================
        # PENGOLAHAN & PENGURANGAN (LOGIKA LAMA DIPERTAHANKAN)
        # =====================================================
        days_period = 609  # Jan 2024 - Aug 2025
        if "total_calc" in df_program.columns:
            df_program["total_calc"] = pd.to_numeric(
                df_program["total_calc"].astype(str).str.replace(",", "."),
                errors="coerce"
            )
            total_program = df_program["total_calc"].sum()
        else:
            total_program = 0

        avg_timbulan_perhari = total_timbulan
        avg_program_perhari = total_program / days_period if days_period > 0 else 0

        if "kategori" in df_program.columns:
            df_pengolahan = df_program[df_program["kategori"] == "Program Pengelolaan"]
            total_pengolahan = df_pengolahan["total_calc"].sum()/days_period if not df_pengolahan.empty else 0
            persen_pengolahan = (total_pengolahan / total_timbulan * 100) if total_timbulan > 0 else 0

            df_pengurangan = df_program[df_program["kategori"] == "Program Pengurangan"]
            total_pengurangan = df_pengurangan["total_calc"].sum()/days_period if not df_pengurangan.empty else 0
            persen_pengurangan = (total_pengurangan / total_timbulan * 100) if total_timbulan > 0 else 0
        else:
            total_pengolahan = persen_pengolahan = total_pengurangan = persen_pengurangan = 0

        total_sisa = total_timbulan - total_pengolahan
        persen_sisa = (total_sisa / total_timbulan * 100) if total_timbulan > 0 else 0
        persen_sisa = min(max(persen_sisa, 0), 100)

        # CSS Card (sesuai versi mas)
        st.markdown("""
            <style>
            .card {border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; background-color: #fff;
                   box-shadow: 3px 3px 12px rgba(0,0,0,0.1); text-align: center; margin-bottom: 5px;}
            .card h3 {font-size: 20px; color: #333; margin-bottom: 5px;}
            .card h2 {font-size: 40px; color: #257d0a; margin: 0;}
            .card p {font-size: 20px; color: #666; margin: 0;}
            </style>
        """, unsafe_allow_html=True)

        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(f"<div class='card'><h3>Pengurangan Sampah (Reduce)</h3><h2>{total_pengurangan:,.0f}</h2><p>kg/hari</p></div>", unsafe_allow_html=True)
        with colB:
            st.markdown(f"<div class='card'><h3>Pengolahan Sampah</h3><h2>{persen_pengolahan:.2f}%</h2><p>{total_pengolahan:,.0f} kg/hari dari timbulan</p></div>", unsafe_allow_html=True)
        with colC:
            st.markdown(f"<div class='card'><h3>Timbulan Tidak Terkelola</h3><h2>{persen_sisa:.2f}%</h2><p>{total_sisa:,.0f} kg/hari</p></div>", unsafe_allow_html=True)


        # =====================================================
        # PETA SITE & CCTV
        # =====================================================
        st.subheader("🗺️ Peta Lokasi Site & CCTV")
        filter_map = st.radio("Pilih data:", ["Timbulan + Site", "CCTV", "Keduanya"], horizontal=True)

        fmap = folium.Map(location=[-2.0, 117.0], zoom_start=6)

        # --- Site Timbulan ---
        if not df_timbulan.empty and not df_koordinat.empty and filter_map in ["Timbulan + Site", "Keduanya"]:
            df_timbulan["company_code"] = company_to_code(df_timbulan.get("perusahaan", ""))
            agg_timbulan = df_timbulan.groupby(["site", "company_code"], as_index=False).agg(
                total_timbulan=("timbulan", "sum")
            )

            if not df_program.empty and "kategori" in df_program.columns:
                df_pengolahan = df_program[df_program["kategori"] == "Program Pengelolaan"].copy()
                df_pengolahan["total_calc"] = pd.to_numeric(df_pengolahan["total_calc"], errors="coerce").fillna(0)
                agg_pengolahan = df_pengolahan.groupby(["site", "perusahaan"], as_index=False).agg(
                    total_pengolahan=("total_calc", "sum")
                )
                agg_pengolahan["company_code"] = company_to_code(agg_pengolahan["perusahaan"])
                agg_pengolahan["sampah_terkelola"] = agg_pengolahan["total_pengolahan"] / days_period
            else:
                agg_pengolahan = pd.DataFrame(columns=["site","company_code","sampah_terkelola"])

            agg = agg_timbulan.merge(
                agg_pengolahan[["site","company_code","sampah_terkelola"]],
                on=["site","company_code"], how="left"
            )
            agg["sampah_terkelola"] = agg["sampah_terkelola"].fillna(0)
            agg["sampah_tidak_terkelola"] = agg["total_timbulan"] - agg["sampah_terkelola"]

            if "x" in df_koordinat.columns and "y" in df_koordinat.columns:
                df_koordinat["x"] = pd.to_numeric(df_koordinat["x"], errors="coerce")
                df_koordinat["y"] = pd.to_numeric(df_koordinat["y"], errors="coerce")
                df_koordinat = df_koordinat.dropna(subset=["x", "y"])
                df_koordinat["company_code"] = company_to_code(df_koordinat.get("company", ""))

                df_map = df_koordinat.merge(agg, on=["site", "company_code"], how="left")
                if not df_map.empty:
                    lon, lat = transformer.transform(df_map["x"].astype(float).values, df_map["y"].astype(float).values)
                    df_map["lon"] = lon; df_map["lat"] = lat

                    for _, r in df_map.iterrows():
                        popup_html = f"""
                        <b>Site:</b> {r.get('site','-')}<br>
                        <b>Perusahaan:</b> {r.get('company_code','-')}<br>
                        <b>Total Timbulan:</b> {r.get('total_timbulan',0):,.0f} kg<br>
                        <b>Sampah Terkelola:</b> {r.get('sampah_terkelola',0):,.2f} kg<br>
                        <b>Sampah Tidak Terkelola:</b> {r.get('sampah_tidak_terkelola',0):,.2f} kg
                        """
                        folium.Marker(
                            location=[r["lat"], r["lon"]],
                            tooltip=f"{r['site']} - {r['company_code']}",
                            popup=popup_html,
                            icon=folium.Icon(color="green", icon="trash", prefix="fa"),
                        ).add_to(fmap)

        # --- CCTV pakai logika pages/5_CCTV.py ---
        if not df_cctv.empty and "easting" in df_cctv.columns and "northing" in df_cctv.columns and filter_map in ["CCTV", "Keduanya"]:
            lon_lat = df_cctv.apply(lambda r: pd.Series(parse_coord(r["easting"], r["northing"]), index=["lon","lat"]), axis=1)
            df_cctv = pd.concat([df_cctv, lon_lat], axis=1)
            valid = df_cctv.dropna(subset=["lat","lon"])
            if not valid.empty:
                unique_perusahaan = sorted(valid["perusahaan"].dropna().unique().tolist())
                for _, row in valid.iterrows():
                    color = assign_color(row["perusahaan"], unique_perusahaan)
                    popup_text = f"""
                    <b>{row.get('nama_titik_penaatan_ts','')}</b><br>
                    {row.get('perusahaan','')} - {row.get('site','')}<br>
                    Coverage: {row.get('coverage_cctv','')}
                    """
                    folium.Marker(
                        location=[float(row["lat"]), float(row["lon"])],
                        popup=popup_text,
                        tooltip=row.get("nama_titik_penaatan_ts",""),
                        icon=folium.Icon(color=color, icon="camera", prefix="fa")
                    ).add_to(fmap)

        st_folium(fmap, height=600, use_container_width=True)

        # =====================================================
        # GRAFIK TIMBULAN (VERSI LAMA – TIDAK DIUBAH)
        # =====================================================
        col1, col2 = st.columns([0.5, 0.5])
        if not df_timbulan.empty and "jenis_timbulan" in df_timbulan.columns:
            jenis_unique = df_timbulan["jenis_timbulan"].unique()
            colors = px.colors.sequential.Viridis[:len(jenis_unique)]
            color_map = {j: c for j, c in zip(jenis_unique, colors)}

            with col1:
                st.markdown('<p style="text-align: center;font-weight: bold;">🥧 Proporsi Timbulan Berdasarkan Jenis</p>', unsafe_allow_html=True)
                jenis_sum = df_timbulan.groupby("jenis_timbulan")["timbulan"].sum()
                fig2 = px.pie(
                    names=jenis_sum.index, values=jenis_sum.values,
                    hole=0.4, color=jenis_sum.index, color_discrete_map=color_map,
                    template="plotly_white"
                )
                fig2.update_traces(textinfo="percent+label", showlegend=True)
                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                st.markdown('<p style="text-align:center;font-weight: bold;">Proporsi Timbulan Per Site</p>', unsafe_allow_html=True)
                total_site = df_timbulan.groupby(["site", "jenis_timbulan"], as_index=False)["timbulan"].sum()
                total_site = total_site.sort_values(by=["site", "timbulan"], ascending=[True, False])
                fig1 = px.bar(
                    total_site, y="site", x="timbulan", color="jenis_timbulan",
                    orientation='h', text="timbulan", template="plotly_white",
                    labels={"timbulan":"Total Timbulan (kg)", "jenis_timbulan":"Jenis Timbulan"},
                    color_discrete_map=color_map, height=400
                )
                fig1.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
                st.plotly_chart(fig1, use_container_width=True)

        # =====================================================
        # 🔹 SURVEI & KETIDAKSESUAIAN
        # =====================================================
        st.subheader("📊 Survei & Ketidaksesuaian")

        # Pie Ketidaksesuaian (Valid)
        if not df_ketidaksesuaian.empty and "kategori_subketidaksesuaian" in df_ketidaksesuaian.columns:
            df_valid = df_ketidaksesuaian[df_ketidaksesuaian["status_temuan"].str.lower() == "valid"]
            if not df_valid.empty:
                prop = df_valid["kategori_subketidaksesuaian"].value_counts()
                fig_ket = px.pie(
                    names=prop.index, values=prop.values, hole=0.4,
                    color=prop.index, template="plotly_white",
                    color_discrete_map={"Perilaku":"#347829","Non Perilaku":"#78b00a"}
                )
                fig_ket.update_traces(textinfo="percent+label")
                st.markdown("<p style='font-weight:bold;text-align:center;'>⚠️ Proporsi Ketidaksesuaian</p>", unsafe_allow_html=True)
                st.plotly_chart(fig_ket, use_container_width=True)

        # Gabung survei online+offline
        df_survey = pd.concat([df_online, df_offline], ignore_index=True)

        # Kolom pertanyaan (biarkan sesuai punyamu)
        col_q = "2. Seberapa optimal program GBST berjalan selama ini di perusahaan Anda?"

        if not df_survey.empty:
            # Kalau nama kolom sedikit berbeda, coba cari yang mirip
            if col_q not in df_survey.columns:
                candidates = [c for c in df_survey.columns if "optimal" in c.lower() and "gbst" in c.lower()]
                if candidates:
                    col_q = candidates[0]

        if col_q in df_survey.columns:
            df_survey[col_q] = pd.to_numeric(df_survey[col_q], errors="coerce")
            df_survey = df_survey.dropna(subset=[col_q])

            if not df_survey.empty:
                avg_score = df_survey[col_q].mean()
                max_score = df_survey[col_q].max()
                max_score = max(max_score, 1)

                gauge_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=avg_score,
                    title={"text": "Rata-rata Skor Optimalitas Program"},
                    gauge={
                        'axis': {'range': [0, max_score]},
                        'bar': {'color': "green"},
                        'steps': [
                            {'range': [0, max_score * 0.5], 'color': "#F58C62"},
                            {'range': [max_score * 0.5, max_score * 0.8], 'color': "#E1EF47"},
                            {'range': [max_score * 0.8, max_score], 'color': "#4CB817"}
                        ]
                    }
                ))
                st.plotly_chart(gauge_fig, use_container_width=True)

            else:
                st.warning("Data survei kosong setelah konversi angka untuk kolom optimalitas.")
        else:
            st.warning(f"Kolom '{col_q}' tidak ditemukan dalam data survei.")

    except Exception as e:
        st.error("Terjadi error di Overview")
        st.exception(e)

with tab2:
    st.subheader("📋 Preview Data Timbulan")
    st.dataframe(df_timbulan.head(100) if not df_timbulan.empty else "Data Timbulan kosong.")
    st.subheader("📋 Preview Data Program")
    st.dataframe(df_program.head(100) if not df_program.empty else "Data Program kosong.")
    st.subheader("📋 Preview Data Ketidaksesuaian")
    st.dataframe(df_ketidaksesuaian.head(100) if not df_ketidaksesuaian.empty else "Data Ketidaksesuaian kosong.")
    st.subheader("📋 Preview Data Survei (Online + Offline)")
    df_survey_preview = pd.concat([df_online, df_offline], ignore_index=True)
    st.dataframe(df_survey_preview.head(100) if not df_survey_preview.empty else "Data Survei kosong.")
    st.subheader("📋 Preview Data Koordinat UTM & CCTV")
    st.dataframe(df_koordinat.head(50) if not df_koordinat.empty else "Data Koordinat kosong.")
    st.dataframe(df_cctv.head(50) if not df_cctv.empty else "Data CCTV kosong.")
