import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================
# Load Data dari Google Sheets
# =============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
sheet_name = ["Timbulan","Program","Survei_Online","Ketidaksesuaian","Survei_Offline","CCTV","Jml_CCTV"]

all_df = {}
for sheet in sheet_name:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")

# Ambil sheet timbulan dan program
dt_timbulan = all_df.get("Timbulan", pd.DataFrame())
dt_program = all_df.get("Program", pd.DataFrame())
df_program = all_df.get("Program", pd.DataFrame())
dt_online = all_df.get("Survei_Online", pd.DataFrame())


# Pastikan kolom numeric
if "Timbulan" in dt_timbulan.columns:
    dt_timbulan["Timbulan"] = pd.to_numeric(dt_timbulan["Timbulan"], errors='coerce').fillna(0)
if "Total_calc" in dt_program.columns:
    dt_program["Total_calc"] = pd.to_numeric(dt_program["Total_calc"], errors='coerce').fillna(0)

# =============================
# FILTER LOKAL (HANYA PAGE INI)
# =============================
import calendar
import re
st.sidebar.subheader("Filter Data")
site_list = sorted(dt_timbulan["Site"].dropna().unique()) if "Site" in dt_timbulan.columns else []
site_sel = st.sidebar.multiselect("Pilih Site", site_list, default=site_list[:4] if site_list else [])

perusahaan_list = sorted(dt_timbulan["Perusahaan"].dropna().unique()) if "Perusahaan" in dt_timbulan.columns else []
perusahaan_sel = st.sidebar.multiselect("Pilih Perusahaan", perusahaan_list, default=perusahaan_list[:6] if perusahaan_list else [])


# 1. Deteksi kolom bulan-tahun otomatis
pattern = r"^(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember) \d{4}$"
bulan_tahun_cols = [col for col in df_program.columns if re.match(pattern, str(col))]

# 2. Reshape wide → long
df_prog_long = df_program.melt(
    id_vars=[col for col in df_program.columns if col not in bulan_tahun_cols],
    value_vars=bulan_tahun_cols,
    var_name="Bulan-Tahun",
    value_name="Value"
)
df_prog_long["Tahun"] = df_prog_long["Bulan-Tahun"].apply(lambda x: int(x.split(" ")[1]))
df_prog_long["Bulan"] = df_prog_long["Bulan-Tahun"].apply(lambda x: x.split(" ")[0])

# 3. Mapping nama bulan ke angka
bulan_map = {
   "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
  "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
  "September": 9, "Oktober": 10, "November": 11, "Desember": 12
}


# 4. Bisa bikin kolom periode datetime (buat filter/plot)
import datetime

df_prog_long["Periode"] = df_prog_long.apply(
    lambda row: datetime.datetime(row["Tahun"], bulan_map[row["Bulan"]], 1),
    axis=1
)
# ======================
# Filter Bulan & Tahun
# ======================
df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame())
df_ketidaksesuaian["TanggalLapor"] = pd.to_datetime(df_ketidaksesuaian["TanggalLapor"], dayfirst=True, errors="coerce")
df_ketidaksesuaian["Tahun"] = df_ketidaksesuaian["TanggalLapor"].dt.year
df_ketidaksesuaian["Bulan"] = df_ketidaksesuaian["TanggalLapor"].dt.month
# Buat filter selectbox
# Pastikan pakai df_ketidaksesuaian yang sudah punya kolom Tahun & Bulan
tahun_tersedia = sorted(df_prog_long["Tahun"].dropna().unique())
#bulan_tersedia = [b for b in calendar.month_name[1:]]  # ['Januari', ..., 'Desember']
bulan_tersedia = list(bulan_map.keys())  


    #tahun_pilihan = st.selectbox("Pilih Tahun:", tahun_tersedia, index=len(tahun_tersedia)-1)
#tahun_pilihan = st.sidebar.multiselect("Pilih Tahun:", tahun_tersedia, default=tahun_tersedia)

#bulan_pilihan = st.sidebar.multiselect("Pilih Bulan:", bulan_tersedia, default=bulan_tersedia)

# Filter dataframe sesuai pilihan user
# Convert nama bulan ke angka untuk filter Ketidaksesuaian
#bulan_pilihan_num = [bulan_map[b] for b in bulan_pilihan]
# =============================
# Apply Filter
# =============================
# Apply filter ke df_program
#df_prog_filtered = df_prog_long[
 #   (df_prog_long["Tahun"].isin(tahun_pilihan)) &
  #  (df_prog_long["Bulan"].isin(bulan_pilihan))
#].sort_values(by=["Tahun","Periode"])

# Apply filter ke df_ketidaksesuaian
#df_ketidaksesuaian["TanggalLapor"] = pd.to_datetime(df_ketidaksesuaian["TanggalLapor"], dayfirst=True, errors="coerce")
#df_ketidaksesuaian["Tahun"] = df_ketidaksesuaian["TanggalLapor"].dt.year
#df_ketidaksesuaian["Bulan"] = df_ketidaksesuaian["TanggalLapor"].dt.month

#df_ket_filtered = df_ketidaksesuaian[
 #   (df_ketidaksesuaian["Tahun"].isin(tahun_pilihan)) &
  #  (df_ketidaksesuaian["Bulan"].isin(bulan_pilihan_num)) &
   # (df_ketidaksesuaian["status_temuan"]=="Valid")
#].sort_values(by=["Tahun","Bulan"])

# Filter Timbulan
df_timbulan_filtered = dt_timbulan.copy()
if site_sel:
    df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["Site"].isin(site_sel)]
if perusahaan_sel:
    df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["Perusahaan"].isin(perusahaan_sel)]

# =============================
# Info Jumlah Hari
# =============================
#if len(bulan_pilihan_num) == 1 and len(tahun_pilihan) == 1:
#    days_period = calendar.monthrange(tahun_pilihan[0], bulan_pilihan_num[0])[1]
 #   st.info(f"📅 Jumlah hari {bulan_pilihan[0]} {tahun_pilihan[0]}: **{days_period} hari**")
#else:
 #   st.info(f"📅 Filter multi-bulan / multi-tahun dipilih, jumlah hari spesifik tidak ditampilkan")

# Apply filter lokal
df_filtered = dt_timbulan.copy()
if site_sel:
    df_filtered= df_filtered[df_filtered["Site"].isin(site_sel)]
if perusahaan_sel:
    df_filtered = df_filtered[df_filtered["Perusahaan"].isin(perusahaan_sel)]


# =============================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

#days_period = 609  # Jan 2024 - Agustus 2025

# Data dasar
dt_timbulan = all_df.get("Timbulan", pd.DataFrame())
dt_program = all_df.get("Program", pd.DataFrame())

# Pastikan numeric
#dt_timbulan["Timbulan"] = pd.to_numeric(dt_timbulan["Timbulan"], errors='coerce').fillna(0)
dt_program['Total_calc'] = pd.to_numeric(dt_program['Total_calc'], errors='coerce').fillna(0)


try:
        # ambil data dari all_df
        df_timbulan = all_df.get("Timbulan", pd.DataFrame())
        df_program = all_df.get("Program", pd.DataFrame())
        df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame())

        # --- col1: Total Timbulan ---
        if "Timbulan" in df_timbulan.columns:
            df_timbulan["Timbulan"] = pd.to_numeric(
                df_timbulan["Timbulan"].astype(str).str.replace(",", "."),
                errors="coerce"
            )
            total_timbulan = df_timbulan["Timbulan"].sum()
            total_timbulan_all = df_timbulan["data_input_total"].sum()

            # Ambil nilai unik dari kolom "Man Power"
            manpower_unique = pd.to_numeric(
                pd.Series(df_timbulan["Man Power"].unique()).astype(str).str.replace(",", "."),
                errors="coerce"
            )

            # Jumlahkan nilai unik manpower
            total_manpower = manpower_unique.sum()

            # Rasio timbulan terhadap total manpower
            rasio_manpower = total_timbulan / total_manpower if total_manpower > 0 else 0
        else:
            total_timbulan = 0
            total_manpower = 0
            rasio_manpower = 0


            # program sheet juga pastikan numeric
        if "Nama program" in df_program.columns:
            df_program["Total_calc"] = pd.to_numeric(df_program["Total_calc"].astype(str).str.replace(",", "."), errors="coerce")
            jumlah_program = df_program["Nama program"].count()
            jumlah_program = df_program["Nama program"].dropna().shape[0]
        else:
            jumlah_program = 0
        # --- col3: Total Ketidaksesuaian Valid ---
        if "status_temuan" in df_ketidaksesuaian.columns:
            total_ketidaksesuaian = df_ketidaksesuaian.query("status_temuan == 'Valid'").shape[0]
            temuan_masuk = df_ketidaksesuaian["status_temuan"].count()
        else:
            total_ketidaksesuaian = 0

            # pastikan numeric dulu
        if "Total_calc" in df_program.columns:
            df_program["Total_calc"] = pd.to_numeric(
                df_program["Total_calc"].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )
            total_program = df_program["Total_calc"].sum()
        else:
            total_program = 0

        # --- col4: Persentase rata-rata sampah yang terkelola/terkurangi ---
        days_period = 609  # periode Jan 2024 - Agustus 2025
        if "Total_calc" in df_program.columns and total_timbulan > 0:
            total_program = df_program["Total_calc"].sum()
            avg_timbulan_perhari = total_timbulan 
            avg_program_perhari = total_program / days_period
            persentase_terkelola = (avg_program_perhari / avg_timbulan_perhari) * 100
        else:
            persentase_terkelola = 0

        # ===============================
        # TAMPILKAN METRIC
        # ===============================
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Total Timbulan          (kg)</h6>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{total_timbulan_all:,.0f}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">per 8 dari <strong>{total_manpower:,}</strong> manpower</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Rata-rata Timbulan (kg/hari)</h6>
                    <p style="font-size:40px; margin:0;margin-top:0;">{total_timbulan:.2f}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;"> dengan <strong>{rasio_manpower:.2f}</strong> kg/hari/manpower</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Jumlah Man Power (Avg/hari)              </h6>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{total_manpower:,}  </p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;"> pekerja</p>
                </div>
            """, unsafe_allow_html=True)

        # ======================================================
        # 🔢 RATA-RATA TIMBULAN SESUAI SNI (kg/hari/orang)
        # ======================================================
        st.markdown("### ♻️ Rata-rata Timbulan Sesuai SNI (kg/hari/orang)")

        if not df_timbulan.empty and {"Site","Perusahaan","Timbulan","Man Power"}.issubset(df_timbulan.columns):
            df_timbulan_sni = df_timbulan.copy()

            # Pastikan numeric
            df_timbulan_sni["Timbulan"] = pd.to_numeric(df_timbulan_sni["Timbulan"], errors="coerce").fillna(0)
            df_timbulan_sni["Man Power"] = pd.to_numeric(df_timbulan_sni["Man Power"], errors="coerce").fillna(0)

            # --- Ambil Man Power unik per kombinasi Site–Perusahaan ---
            df_mp_unik = (
                df_timbulan_sni.drop_duplicates(subset=["Site","Perusahaan"], keep="last")[["Site","Perusahaan","Man Power"]]
            )

            # Total timbulan (semua baris terfilter)
            total_timbulan_all = df_timbulan_sni["Timbulan"].sum()

            # Total manpower unik (tanpa duplikat)
            total_mp_unik = df_mp_unik["Man Power"].sum()

            # Rata-rata timbulan per orang
            rata_sni = total_timbulan_all / total_mp_unik if total_mp_unik > 0 else 0

            st.markdown(f"""
            <div style="background:#f8fff5;border:1px solid #a5d6a7;border-radius:8px;padding:15px;margin-bottom:10px;">
                <h5 style="margin:0;color:#2e7d32;">Rata-rata Timbulan (SNI)</h5>
                <p style="font-size:32px;margin:0;color:#1b5e20;"><strong>{rata_sni:.3f}</strong> kg/hari/orang</p>
                <p style="font-size:13px;margin-top:4px;color:#388e3c;">Total Timbulan: {total_timbulan_all:,.0f} kg | Total Man Power Unik: {total_mp_unik:,}</p>
            </div>
            """, unsafe_allow_html=True)

            # --- Tabel per site untuk transparansi ---
            st.markdown("#### 📋 Rincian per Site")
            df_site_sni = (
                df_timbulan_sni.groupby("Site", as_index=False)
                .agg(total_timbulan=("Timbulan","sum"))
                .merge(
                    df_mp_unik.groupby("Site", as_index=False)["Man Power"].sum(),
                    on="Site", how="left"
                )
            )
            df_site_sni["kg/hari/orang"] = (df_site_sni["total_timbulan"] / df_site_sni["Man Power"]).round(3)
            df_site_sni = df_site_sni.sort_values("kg/hari/orang", ascending=False)
            st.dataframe(df_site_sni, hide_index=True)

        else:
            st.warning("Kolom 'Timbulan', 'Man Power', 'Site', atau 'Perusahaan' belum lengkap untuk perhitungan SNI.")

except Exception as e:
        st.error("Gagal menghitung metric.")
        st.exception(e)



# --- KPI ---
total_timbulan = dt_timbulan['Timbulan'].sum()
jumlah_program = dt_program.shape[0]
avg_perhari = dt_program['Total_calc'].sum() / days_period if days_period>0 else 0
with st.container():
    col1, col2 = st.columns([0.5,0.5])

    with col1:
        st.markdown('<p style="text-align: center;font-weight: bold;">📊Total Timbulan per Site</p>', unsafe_allow_html=True)
        if not dt_timbulan.empty:
            total_site_timbulan= dt_timbulan.groupby("Site", as_index=False)["Timbulan"].sum()

            # Ambil unique manpower per site-perusahaan
            manpower_unique = dt_timbulan[["Site", "Perusahaan", "Man Power"]].drop_duplicates()
            manpower_site = manpower_unique.groupby("Site", as_index=False)["Man Power"].sum()

            # Gabungkan timbulan + manpower
            total_site = total_site_timbulan.merge(manpower_site, on="Site", how="left")

            fig1 = px.bar(total_site,
                        x="Site",
                        y="Timbulan",
                        text="Timbulan",
                        color="Timbulan",
                        color_continuous_scale=[
                        "#b7e4c7",  # hijau muda
                        "#52b788",  # hijau sedang
                        "#1b4332"   # hijau tua
                        ],
                        labels={"Timbulan":"Total Timbulan (kg)"},
                        template="plotly_white")
            fig1.update_traces(texttemplate="%{text:,.0f}", textposition="outside",hovertemplate=(
                "<b>Site:</b> %{x}<br>" +
                "<b>Total Timbulan:</b> %{y:,.0f} kg<br>" +
                "<b>Man Power:</b> %{customdata[0]:,.0f}<br>" +
                "<extra></extra>"),
                customdata=total_site[["Man Power"]].values)
            fig1.update_layout(height=400,width=800, margin=dict(t=50, b=100))
            st.plotly_chart(fig1, use_container_width=True)


    with col2:
        st.markdown('<p style="text-align: center;font-weight: bold;">📊 Timbulan per Perusahaan - Site</p>', unsafe_allow_html=True)
        if not dt_timbulan.empty and "Perusahaan" in dt_timbulan.columns:
            total_perusahaan = dt_timbulan.groupby(["Perusahaan","Site"], as_index=False)["Timbulan"].sum()
            total_perusahaan["Perusahaan_Site"] = total_perusahaan["Perusahaan"] + " - " + total_perusahaan["Site"]
            # Ambil unique manpower per site-perusahaan
            manpower_unique = dt_timbulan[["Site", "Perusahaan", "Man Power"]].drop_duplicates()
            manpower_site_mitra = manpower_unique.groupby(["Site", "Perusahaan"], as_index=False)["Man Power"].sum()

            # Gabungkan timbulan + manpower
            total_manpower_perusahaan = total_perusahaan.merge(manpower_site_mitra, on=["Site", "Perusahaan"], how="left", suffixes=("", "_y"))
            fig1b = px.bar(
                    total_perusahaan,
                    y="Perusahaan_Site",   # pakai y biar horizontal
                    x="Timbulan",
                    text="Timbulan",
                    color="Timbulan",
                    color_continuous_scale=["#b7e4c7", "#52b788", "#1b4332"],
                    labels={"Timbulan": "Total Timbulan (kg)", "Perusahaan_Site": "Perusahaan - Site"},
                    template="plotly_white",
                    orientation="h"   # ini penting buat horizontal
                )

            fig1b.update_traces(
                    texttemplate="%{text:,.0f}",
                    textposition="outside",
                    hovertemplate=(
                "<b>Total Timbulan:</b> %{x:,.0f} kg<br>" +
                "<b>Man Power:</b> %{customdata[1]:,.0f}<br>" +
                "<extra></extra>"),
                    customdata=total_manpower_perusahaan[["Perusahaan","Man Power"]].values)

            fig1b.update_layout(
                    height=400, width=800,
                    margin=dict(t=50, b=50),
                    yaxis=dict(autorange="reversed"),  # biar ranking terbesar di atas
                    coloraxis_colorbar=dict(
                        title=dict(text="Total Timbulan (kg/hari)",
                        side="right",font=dict(size=10)),   # kecilin font judul
                    tickfont=dict(size=9),     # kecilin font angka
                    thickness=12,              # ketebalan bar warna
                    len=0.6,                   # panjang bar (0-1 proporsi tinggi grafik)
                    x=1.05)                     # geser ke kanan (default 1.0)
            )
            st.plotly_chart(fig1b, use_container_width=True)

    # ===========================
    # BUAT FILTER ORGANIK ANORGANIK
    # ===========================
    # --- Filter checkbox Jenis sampah---
    st.markdown('<p style="text-align:center;font-weight: bold;">🗑️ Filter Jenis Sampah</p>', unsafe_allow_html=True)

    # hasil filter
    jenis_pilihan = dt_timbulan["jenis_sampah"].dropna().unique().tolist() if "jenis_sampah" in dt_timbulan.columns else []
   
    cl1, cl2 = st.columns(2)
    with cl1:
        pilih_organik = st.checkbox("Organik", value=True)  # default tercentang
    with cl2:
        pilih_anorganik = st.checkbox("Anorganik", value=True)  # default tercentang
    

    df_filterjensampah = dt_timbulan[dt_timbulan["jenis_sampah"].isin(jenis_pilihan)]

    with st.container():
        if pilih_organik and not pilih_anorganik:
            df_filterjensampah = dt_timbulan[dt_timbulan["jenis_sampah"] == "Organik"]
        elif pilih_anorganik and not pilih_organik:
            df_filterjensampah = dt_timbulan[dt_timbulan["jenis_sampah"] == "Anorganik"]
        elif not (pilih_organik or pilih_anorganik):
            # kosong tapi kolom tetap ada
            df_filterjensampah = pd.DataFrame(columns=dt_timbulan.columns)
            df_filterjensampah = dt_timbulan
        else:
            df_filterjensampah = dt_timbulan



    # Agregasi per jenis sampah
    #with st.container():
    # Pilih palette yang sama seperti pie chart (Viridis)
    if not dt_timbulan.empty and "jenis_timbulan" in dt_timbulan.columns:
        jenis_unique = dt_timbulan["jenis_timbulan"].unique()
        colors = px.colors.sequential.Viridis[:len(jenis_unique)]  # sesuaikan jumlah warna
        color_map = {j: c for j, c in zip(jenis_unique, colors)}
    
        col1, col2 = st.columns([0.35,0.65])
        with col1:
            st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Sampah Organik vs Anorganik</p>', unsafe_allow_html=True)
            proporsi = df_filterjensampah.groupby("jenis_sampah", as_index=False)["Timbulan"].sum()
            fig1 = px.pie(
                proporsi, 
                names="jenis_sampah", 
                values="Timbulan", 
                hole=0.4, 
                color="jenis_sampah",
                color_discrete_map={"Organik":"#1a5b1d", "Anorganik":"#d3d30e"}
            )
            fig1.update_traces(textinfo="percent+label", pull=[0.01]*len(proporsi))
            fig1.update_layout( showlegend = False)
            st.plotly_chart(fig1, use_container_width=True)

            
        with col2:
            st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Timbulan per Perusahaan - Site</p>', unsafe_allow_html=True)
            #color_map = {"Organik": "#1a5b1d", "Anorganik": "#d3d30e"}
            
            if not df_filterjensampah.empty and "Perusahaan" in df_filterjensampah.columns:
                # Total timbulan per perusahaan-site per jenis sampah
                total_perusahaan = df_filterjensampah.groupby(["Perusahaan", "Site", "jenis_sampah"], as_index=False)["Timbulan"].sum()
                total_perusahaan["Perusahaan_Site"] = total_perusahaan["Perusahaan"] + " - " + total_perusahaan["Site"]
                
                # Bar chart horizontal
                fig3 = px.bar(
                    total_perusahaan,
                    y="Perusahaan_Site",
                    x="Timbulan",
                    text="Timbulan",
                    color="jenis_sampah",
                    color_discrete_map={"Organik": "#1a5b1d", "Anorganik": "#d3d30e"},
                    labels={"Timbulan": "Total Timbulan (kg)", "Perusahaan_Site": "Perusahaan - Site"},
                    template="plotly_white",
                    orientation="h"
                )
                
                fig3.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig3.update_layout(
                    height=500, width=800,
                    margin=dict(t=50, b=50),
                    xaxis_title="Total Timbulan (kg)",
                    yaxis_title="Perusahaan - Site",
                    barmode="stack",  # ini biar proporsinya terlihat
                    bargap = 0.2,
                    legend=dict(orientation="h",font=dict(size=8),
                    yanchor="top",
                    y=1.2,                   # agak jauh ke bawah
                    x=0.2,
                    xanchor="center",
                    traceorder="normal",       # biar urut sesuai data
                    valign="top"
                ))
                
                st.plotly_chart(fig3, use_container_width=True)

        col1,col2 = st.columns([0.4,0.6])
        with col1:
            st.markdown('<p style="text-align: left;font-weight: bold;">🔎 Proporsi Detail per Jenis Timbulan</p>', unsafe_allow_html=True)
            jenis_detail = df_filterjensampah.groupby("jenis_timbulan", as_index=False)["Timbulan"].sum()
            fig2 = px.pie(
                jenis_detail, 
                names="jenis_timbulan", 
                values="Timbulan", 
                color="jenis_timbulan",
                hole=0.3,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig2.update_traces(textinfo="percent+label", pull=[0.01]*len(jenis_detail))
            fig2.update_layout(showlegend = False)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Detail Timbulan per perusahaan - Site</p>', unsafe_allow_html=True)
            if not df_filterjensampah.empty and "Perusahaan" in df_filterjensampah.columns:
                total_perusahaan_detail = df_filterjensampah.groupby(
                ["Perusahaan","Site","jenis_timbulan"], as_index=False
                )["Timbulan"].sum()
                total_perusahaan_detail["Perusahaan_Site"] = (
                total_perusahaan_detail["Perusahaan"] + " - " + total_perusahaan_detail["Site"]
                )

            fig4 = px.bar(
                total_perusahaan_detail,
                x="Perusahaan_Site",   # jadi x
                y="Timbulan",          # jadi y
                text="Timbulan",
                color="jenis_timbulan",
                #colors=color_map,  # pakai color_map yang sudah dibuat
                color_discrete_map=color_map,  # pakai color_map yang sudah dibuat
                labels={
                    "Timbulan":"Total Timbulan (kg)",
                    "Perusahaan_Site":"Perusahaan - Site",
                    "jenis_timbulan":"Jenis Timbulan"
                },
                template="plotly_white"
            )

            fig4.update_traces(texttemplate="%{text:,.0f}", textposition="inside")
            # fig4.update_layout(
            #     height=400, width=400,
            #     margin=dict(t=50, b=100),
            #     xaxis_title="Perusahaan - Site",
            #     yaxis_title="Total Timbulan (kg)"
            # )
            # Cari nilai maksimum untuk atur rentang dan interval tick
            y_max = total_perusahaan_detail["Timbulan"].max()
            # tentukan interval otomatis: misalnya total/10
            y_dtick = max(int(y_max/5), 1)
            fig4.update_layout(
                height=500, width=800,           
                barmode='stack',
                margin=dict(t=30, b=50, l=100, r=20),
                yaxis=dict(tickmode='linear', dtick=100),
                xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
                bargap=0.2,
                legend=dict(orientation="h",font=dict(size=8),
                    yanchor="top",
                    y=1.2,                   # agak jauh ke bawah
                    x=0.8,
                    xanchor="center",
                    traceorder="normal",       # biar urut sesuai data
                    valign="top"               # rapikan vertikal
            ))
            st.plotly_chart(fig4, use_container_width=True)



    # ===========================
    # RASIO TIMBULAN vs MANPOWER masing" perusahaan
    # ===========================
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    
#------------------------------

     # Ambil unique manpower per site-perusahaan
    manpower_unique = dt_timbulan[["Site", "Perusahaan", "Man Power"]].drop_duplicates()
    timbulan_agg = manpower_unique.groupby(["Site", "Perusahaan"], as_index=False)["Man Power"].sum()
    timbulan_site_perusahaan = dt_timbulan.groupby(["Site", "Perusahaan"], as_index=False)["Timbulan"].sum()
    
    # Gabungkan timbulan + manpower
    #total_manpower_perusahaan = total_perusahaan.merge(manpower_site_mitra, on=["Site", "Perusahaan"], how="left", suffixes=("", "_y"))
    df_agg = timbulan_site_perusahaan.merge(
    timbulan_agg,
    on=["Perusahaan","Site"],
    how="left")
    # Hitung rasio
    df_agg["Rasio_Timbulan"] = df_agg["Timbulan"] / df_agg["Man Power"]

    # Hitung z-score
    mean_ratio = df_agg["Rasio_Timbulan"].mean()
    std_ratio = df_agg["Rasio_Timbulan"].std()
    df_agg["Zscore"] = (df_agg["Rasio_Timbulan"] - mean_ratio) / std_ratio

    # Kategorisasi berbasis z-score
    def kategori(z):
        if abs(z) <= 1.00:
            return "Normal/Wajar"
        elif abs(z) <= 2.00:
            return "Siaga"
        else:
            return "Tidak Wajar"

    df_agg["Kategori"] = df_agg["Zscore"].apply(kategori)

    # Gabungkan Perusahaan - Site jadi satu label
    df_agg["Perusahaan_Site"] = df_agg["Perusahaan"] + " - " + df_agg["Site"]

    # Warna kategori
    color_map = {
        "Normal/Wajar":"#1a9850",
        "Siaga":"#fee08b",
        "Tidak Wajar":"#d73027"
    }
    col1,col2 = st.columns([0.65,0.35])
    with col1:
        # Hitung Q1, Q3 dan IQR
        Q1 = df_agg["Rasio_Timbulan"].quantile(0.25)
        Q3 = df_agg["Rasio_Timbulan"].quantile(0.75)
        IQR = Q3 - Q1

      
        def kategori_iqr(r):
            if r<= Q3 :
                return "Normal"
            elif Q1 - 1.5*IQR <= r < Q1 or Q3 < r <= Q3 + 1.5*IQR:
                return "Siaga"
            else:
                return "Tidak Normal"

        df_agg["Kategori"] = df_agg["Rasio_Timbulan"].apply(kategori_iqr)
        df_agg["Perusahaan_Site"] = df_agg["Perusahaan"] + " - " + df_agg["Site"]

        # Warna kategori
        color_map = {
            "Normal": "#1a9850",
            "Siaga": "#fee08b",
            "Tidak Normal": "#d73027"
        }

        # --- VISUALISASI ---
        st.markdown('<p style="text-align: left;font-weight: bold;">⚖️ Rasio Timbulan/Manpower</p>', unsafe_allow_html=True)

        fig = px.bar(
            df_agg,
            x="Perusahaan_Site",
            y="Rasio_Timbulan",
            color="Kategori",
            color_discrete_map=color_map,
            text=df_agg["Rasio_Timbulan"].round(2),
            labels={"Rasio_Timbulan":"Rasio Timbulan per Manpower (kg/orang)"},
            template="plotly_white"
        )

        # Tambahkan garis threshold IQR
        fig.add_hline(y=Q1, line_dash="dot", line_color="green", annotation_text=f"Q1 = {Q1:.2f}", annotation_position="bottom left")
        fig.add_hline(y=Q3, line_dash="dot", line_color="green", annotation_text=f"Q3 = {Q3:.2f}", annotation_position="top left")
        fig.add_hline(y=Q3 + 1.5*IQR, line_dash="dash", line_color="orange", annotation_text=f"Batas Siaga = {Q3 + 1.5*IQR:.2f}", annotation_position="top right")

        # Update layout
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis=dict(tickangle=-30),
            margin=dict(t=40, b=120, l=50, r=50),
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
        )

        st.plotly_chart(fig, use_container_width=True)

        
      
        # Tampilkan tabel ringkasan
        #st.dataframe(df_agg[["Perusahaan_Site","Timbulan","Man Power","Rasio_Timbulan","Zscore","Kategori"]])
    with col2:
    # --- VISUALISASI BOX PLOT Z-SCORE ---
        st.markdown('<p style="text-align: left;font-weight: bold;">📦 Distribusi Z-score Rasio Timbulan/Manpower</p>', unsafe_allow_html=True)

        fig_box = px.box(
            df_agg,
            y="Zscore",
            points="all",  # tampilkan semua titik perusahaan-site
            hover_data=["Perusahaan_Site", "Rasio_Timbulan"],
            labels={"Zscore":"Z-score Rasio Timbulan"},
            template="plotly_white"
        )

        fig_box.update_traces(
            jitter=0.3, 
            marker=dict(size=8, color="darkblue", line=dict(width=1, color="white"))
        )

        fig_box.update_layout(
            margin=dict(t=40, b=40, l=50, r=50),
            yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor="red")
        )

        st.plotly_chart(fig_box, use_container_width=True)
      # --- TABEL RINGKASAN SEBAGAI DROPDOWN ---
    with st.expander("Detail Data Rasio Timbulan per Manpower"):
        st.dataframe(df_agg[["Perusahaan_Site","Timbulan","Man Power","Rasio_Timbulan","Zscore","Kategori"]])


    # ===========================
    # =============================
    # Apply filter
    # =============================
    df_filtered = dt_timbulan.copy()
    if site_sel:
        df_filtered = df_filtered[df_filtered["Site"].isin(site_sel)]
    if perusahaan_sel:
        df_filtered = df_filtered[df_filtered["Perusahaan"].isin(perusahaan_sel)]

    if pilih_organik and not pilih_anorganik:
        df_filtered = df_filtered[df_filtered["jenis_sampah"] == "Organik"]
    elif pilih_anorganik and not pilih_organik:
        df_filtered = df_filtered[df_filtered["jenis_sampah"] == "Anorganik"]
    elif not (pilih_organik or pilih_anorganik):
        df_filtered = pd.DataFrame(columns=dt_timbulan.columns)  # kosong tapi kolom tetap ada



#=====================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =============================
# 1️⃣ Load data
# =============================
# df_filtered = pd.read_excel("data.xlsx")  # ganti sesuai file

# Mapping rho (kg/L) per jenis_timbulan
rho_map = {
    "Kardus": 0.02,
    "Botol Plastik": 0.01,
    "Organik Lainnya": 0.12,
    "Lainnya": 0.01,
    "Sisa Makanan & Sayur": 0.12,
    "Kertas": 0.02,
    "Plastik": 0.01,
    "Organik": 0.12
}

# Tambahkan kolom rho dan konversi Timbulan (kg → liter)
df_filtered['rho'] = df_filtered['jenis_timbulan'].map(rho_map)
df_filtered['Timbulan_Volume'] = df_filtered['Timbulan'] / df_filtered['rho']

# =============================
# 2️⃣ Definisikan kategori besar
# =============================
organik_list = ["Organik", "Organik Lainnya", "Sisa Makanan & Sayur"]
anorganik_list = ["Kardus", "Botol Plastik", "Plastik", "Kertas", "Lainnya"]

# =============================
# 3️⃣ Aggregate per Site-Perusahaan
# =============================
df_grouped = df_filtered.groupby(
    ['Site', 'Perusahaan', 'jenis_timbulan', 'jenis_sampah', 'Kapasitas', 'Kapasitas.1'], 
    as_index=False
).agg({'Timbulan_Volume':'sum'})

# Hitung total volume Organik / Anorganik
df_grouped['Timbulan_Organik_Volume'] = np.where(df_grouped['jenis_timbulan'].isin(organik_list), 
                                                 df_grouped['Timbulan_Volume'], 0)
df_grouped['Timbulan_Anorganik_Volume'] = np.where(df_grouped['jenis_timbulan'].isin(anorganik_list), 
                                                   df_grouped['Timbulan_Volume'], 0)

# Aggregate final per Site-Perusahaan
df_pivot = df_grouped.groupby(['Site','Perusahaan'], as_index=False).agg({
    'Timbulan_Organik_Volume':'sum',
    'Timbulan_Anorganik_Volume':'sum',
    'Kapasitas':'max',
    'Kapasitas.1':'max'
}).rename(columns={'Kapasitas':'Kapasitas_Organik','Kapasitas.1':'Kapasitas_Anorganik'})

# =============================
# 4️⃣ Kategori kapasitas dengan ikon
# =============================
def kategori_icon(timbulan, kapasitas):
    if timbulan < 0.7 * kapasitas:
        return '✅'
    elif timbulan <= kapasitas:
        return '⚠️'
    else:
        return '❌'

df_pivot['Status_Organik'] = df_pivot.apply(lambda r: kategori_icon(r['Timbulan_Organik_Volume'], r['Kapasitas_Organik']), axis=1)
df_pivot['Status_Anorganik'] = df_pivot.apply(lambda r: kategori_icon(r['Timbulan_Anorganik_Volume'], r['Kapasitas_Anorganik']), axis=1)

# Text untuk chart
text_organik = df_pivot['Timbulan_Organik_Volume'].round(1).astype(str) + " L | " + df_pivot["Status_Organik"]
text_anorganik = df_pivot['Timbulan_Anorganik_Volume'].round(1).astype(str) + " L | " + df_pivot["Status_Anorganik"]

# Label perusahaan-site
df_pivot['Perusahaan_Site'] = df_pivot['Perusahaan'] + '-' + df_pivot['Site']
perusahaan_list = df_pivot['Perusahaan_Site']

# =============================
# 5️⃣ Streamlit Dashboard - Chart
# =============================
col1, col2 = st.columns([0.65,0.35])
with col1:
    st.markdown('<p style="text-align: left;font-weight: bold;">⚖️ Timbulan vs Kapasitas Tempat Sampah</p>', unsafe_allow_html=True)
    color_map = {"Organik": "#1a5b1d", "Anorganik": "#d3d30e"}

    fig = go.Figure()

    # Background kapasitas
    fig.add_trace(go.Bar(
        y=perusahaan_list,
        x=df_pivot['Kapasitas_Anorganik'],
        name='Kapasitas Anorganik',
        orientation='h',
        marker_color=color_map['Anorganik'],
        opacity=0.2,
        text=text_anorganik,
        textposition="outside",
        width=0.4,
        offset=-0.2
    ))
    fig.add_trace(go.Bar(
        y=perusahaan_list,
        x=df_pivot['Kapasitas_Organik'],
        name='Kapasitas Organik',
        orientation='h',
        marker_color=color_map['Organik'],
        opacity=0.2,
        text=text_organik,
        textposition="outside",
        width=0.4,
        offset=0.2
    ))

    # Bar Timbulan
    fig.add_trace(go.Bar(
        y=perusahaan_list,
        x=df_pivot['Timbulan_Anorganik_Volume'],
        name='Timbulan Anorganik',
        orientation='h',
        marker_color=color_map['Anorganik'],
        width=0.4,
        offset=-0.2
    ))
    fig.add_trace(go.Bar(
        y=perusahaan_list,
        x=df_pivot['Timbulan_Organik_Volume'],
        name='Timbulan Organik',
        orientation='h',
        marker_color=color_map['Organik'],
        width=0.4,
        offset=0.2
    ))

    fig.update_layout(
        barmode='overlay',
        xaxis_title="Volume Timbulan / Kapasitas (liter)",
        yaxis_title="Perusahaan-Site (dengan Status)",
        legend_title="Jenis / Kategori",
        yaxis=dict(autorange="reversed"),
        legend=dict(
            orientation="h",
            font=dict(size=9),
            yanchor="top",
            y=1.2,
            x=0.2,
            xanchor="center",
            traceorder="normal"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

#2222222222222222222222222222222
    # =============================
        # Hitung rasio & kategori kapasitas
        # =============================
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go

    # =============================
    # 1️⃣ Load data
    # =============================
    # df_filtered = pd.read_excel("data.xlsx") # ganti sesuai file
    # Mapping rho (kg/L) per jenis timbulan
    rho_map = {
        "Kardus": 0.02,
        "Botol Plastik": 0.01,
        "Organik Lainnya": 0.12,
        "Lainnya": 0.01,
        "Sisa Makanan & Sayur": 0.12,
        "Kertas": 0.02,
        "Plastik": 0.01,
        "Organik": 0.12
    }
    # Tambahkan kolom rho sesuai jenis_sampah
    df_filtered['rho'] = df_filtered['jenis_timbulan'].map(rho_map)

    # Konversi Timbulan (kg) -> Volume (liter)
    df_filtered['Timbulan_Volume'] = df_filtered['Timbulan'] / df_filtered['rho']


    # =============================
    # 2️⃣ Aggregate per Site-Perusahaan & hitung rasio
    # =============================

    df_grouped = df_filtered.groupby(
        ['Site','Perusahaan','jenis_sampah','jenis_timbulan','Kapasitas','Kapasitas.1'], 
        as_index=False
    ).agg({'Timbulan_Volume':'sum'})
   # df_grouped = df_filtered.groupby(
    #    ['Site','Perusahaan','jenis_sampah','jenis_timbulan','Kapasitas','Kapasitas.1'], as_index=False
    #).agg({'Timbulan_Volume':'sum'})

      # Definisikan kategori besar
    organik_list = ["Organik", "Organik Lainnya", "Sisa Makanan & Sayur"]
    anorganik_list = ["Kardus", "Botol Plastik", "Plastik", "Kertas", "Lainnya"]


    # =============================
    # Aggregate per Site-Perusahaan
    # =============================

    # =============================
    # 3️⃣ Tambahkan kolom untuk masing-masing kategori
    # =============================
    df_filtered['Timbulan_Organik_Volume'] = np.where(
        df_filtered['jenis_sampah'].isin(organik_list),
        df_filtered['Timbulan_Volume'],
        0
    )

    df_filtered['Timbulan_Anorganik_Volume'] = np.where(
        df_filtered['jenis_sampah'].isin(anorganik_list),
        df_filtered['Timbulan_Volume'],
        0
    )

    # =============================
    # 4️⃣ Aggregate per Site-Perusahaan
    # =============================
    df_pivot = df_filtered.groupby(['Site','Perusahaan'], as_index=False).agg({
        'Timbulan_Organik_Volume':'sum',
        'Timbulan_Anorganik_Volume':'sum',
        'Kapasitas':'max',       # kapasitas organik
        'Kapasitas.1':'max'      # kapasitas anorganik
    }).rename(columns={'Kapasitas':'Kapasitas_Organik','Kapasitas.1':'Kapasitas_Anorganik'})
    


    # =============================
    # Kategori kapasitas dengan ikon
    # =============================
    def kategori_icon(timbulan, kapasitas):
        if timbulan < 0.7 * kapasitas:
            return '✅'
        elif timbulan <= kapasitas:
            return '⚠️'
        else:
            return '❌'

    df_pivot['Kategori_Organik'] = df_pivot.apply(
        lambda row: kategori_icon(row['Timbulan_Organik_Volume'], row['Kapasitas_Organik']), axis=1
    )
    df_pivot['Kategori_Anorganik'] = df_pivot.apply(
        lambda row: kategori_icon(row['Timbulan_Anorganik_Volume'], row['Kapasitas_Anorganik']), axis=1
    )
        # Tambah kategori status dengan ikon
    df_pivot["Status_Organik"] = df_pivot.apply(
        lambda r: kategori_icon(r["Timbulan_Organik_Volume"], r["Kapasitas_Organik"]), axis=1
    )
    df_pivot["Status_Anorganik"] = df_pivot.apply(
        lambda r: kategori_icon(r["Timbulan_Anorganik_Volume"], r["Kapasitas_Anorganik"]), axis=1
    )
        # Untuk Anorganik
    text_anorganik = df_pivot['Timbulan_Anorganik_Volume'].round(1).astype(str) + " L | " + df_pivot["Status_Anorganik"]

    # Untuk Organik
    text_organik = df_pivot['Timbulan_Organik_Volume'].round(1).astype(str) + " L | " + df_pivot["Status_Organik"]


    # Gabungkan label perusahaan-site dengan ikon
    df_pivot['Perusahaan_Site'] = (
        df_pivot['Perusahaan'] + '-' + df_pivot['Site']
    )
    perusahaan_list = df_pivot['Perusahaan_Site']

    # =============================
    # Streamlit Dashboard - Chart
    # =============================
    col1, col2 = st.columns([0.65,0.35])
    with col1:
        st.markdown('<p style="text-align: left;font-weight: bold;">⚖️ Timbulan vs Kapasitas Tempat Sampah</p>', unsafe_allow_html=True)

        color_map = {"Organik": "#1a5b1d", "Anorganik": "#d3d30e"}

        fig = go.Figure()

        # Background kapasitas (tipis)
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot['Kapasitas_Anorganik'],
            name='Kapasitas Anorganik',
            orientation='h',
            marker_color=color_map['Anorganik'],
            opacity=0.2,
            text=text_anorganik,
            textposition="outside",
            width=0.4,
            offset=-0.2
        ))
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot['Kapasitas_Organik'],
            name='Kapasitas Organik',
            orientation='h',
            marker_color=color_map['Organik'],
            text = text_organik,
            textposition="outside",
            opacity=0.2,
            width=0.4,
            offset=0.2
        ))

        # Bar Timbulan (volume)
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot['Timbulan_Anorganik_Volume'],
            name='Timbulan Anorganik',
            orientation='h',
            marker_color=color_map['Anorganik'],
            
            width=0.4,
            offset=-0.2
        ))
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot['Timbulan_Organik_Volume'],
            name='Timbulan Organik',
            orientation='h',
            marker_color=color_map['Organik'],
            
            width=0.4,
            offset=0.2
        ))

        fig.update_layout(
            barmode='overlay',
            xaxis_title="Volume Timbulan / Kapasitas (liter)",
            yaxis_title="Perusahaan-Site (dengan Status)",
            legend_title="Jenis / Kategori",
            yaxis=dict(autorange="reversed"),
            legend=dict(
                orientation="h",
                font=dict(size=9),
                yanchor="top",
                y=1.2,
                x=0.2,
                xanchor="center",
                traceorder="normal"
            )
        )

        st.plotly_chart(fig, use_container_width=True)


    # =============================
    # Tabel CCTV per Perusahaan-Site
    # =============================
    df_cctv = all_df.get("Jml_CCTV", pd.DataFrame())
    if not df_cctv.empty and {"Site","Perusahaan","Coverage 24jam","Coverage non 24jam","Tidak tercover","Total CCTV"}.issubset(df_cctv.columns):
        df_cctv_filtered = df_cctv.copy()
        if site_sel:
            df_cctv_filtered = df_cctv_filtered[df_cctv_filtered["Site"].isin(site_sel)]
        if perusahaan_sel:
            df_cctv_filtered = df_cctv_filtered[df_cctv_filtered["Perusahaan"].isin(perusahaan_sel)]

        #st.markdown('<p style="text-align: left;font-weight: bold;">📋 Tabel CCTV per Perusahaan-Site</p>', unsafe_allow_html=True)
        df_cctv_filtered["Perusahaan_Site"] = df_cctv_filtered["Perusahaan"] + "-" + df_cctv_filtered["Site"]
        #st.dataframe(df_cctv_filtered[["Perusahaan_Site","Coverage 24jam","Coverage non 24jam","Tidak tercover","Total CCTV"]])

        # =============================
        #Visualisasi  CCTV per perusahaan - site, stacked bar
        #=============================
        

        # Buat stacked bar chart
    with col2:
        st.markdown('<p style="text-align: left;font-weight: bold;">📊 Visualisasi CCTV per Perusahaan-Site</p>', unsafe_allow_html=True)
        fig = go.Figure()

        for i, row in df_cctv_filtered.iterrows():
            fig.add_trace(go.Bar(
                x=[row['Coverage 24jam'], row['Coverage non 24jam'], row['Tidak tercover']],
                y=[row['Perusahaan_Site']] * 4,
                name=row['Perusahaan_Site'],
                orientation='h',
                text=[row['Coverage 24jam'], row['Coverage non 24jam'], row['Tidak tercover']],
                marker=dict(color=['#1a9850']),
                  
            ))

        fig.update_layout(
            barmode='stack',
            xaxis_title="Jumlah CCTV",
            yaxis_title="Perusahaan-Site",
            showlegend=False, 
        )

        st.plotly_chart(fig, use_container_width=True)


with st.expander("Detail Timbulan & Kapasitas per Perusahaan-Site"):
        st.dataframe(df_pivot)
