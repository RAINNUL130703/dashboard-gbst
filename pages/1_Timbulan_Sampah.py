import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
import re
import datetime

# =============================
# Load Data dari Google Sheets
# =============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
sheet_name = ["Timbulan", "Program", "Survei_Online",
              "Ketidaksesuaian", "Survei_Offline", "CCTV", "Jml_CCTV"]

all_df = {}
for sheet in sheet_name:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")
        all_df[sheet] = pd.DataFrame()

# Ambil sheet utama
dt_timbulan = all_df.get("Timbulan", pd.DataFrame())
dt_program = all_df.get("Program", pd.DataFrame())
df_program = dt_program.copy()
dt_online = all_df.get("Survei_Online", pd.DataFrame())
df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame())
df_cctv = all_df.get("Jml_CCTV", pd.DataFrame())

# Pastikan kolom numeric dasar
if "Timbulan" in dt_timbulan.columns:
    dt_timbulan["Timbulan"] = pd.to_numeric(
        dt_timbulan["Timbulan"], errors="coerce"
    ).fillna(0)

if "Total_calc" in dt_program.columns:
    dt_program["Total_calc"] = pd.to_numeric(
        dt_program["Total_calc"], errors="coerce"
    ).fillna(0)

# =============================
# FILTER SIDEBAR
# =============================
st.sidebar.subheader("Filter Data")

site_list = sorted(dt_timbulan["Site"].dropna().unique()) if "Site" in dt_timbulan.columns else []
site_sel = st.sidebar.multiselect("Pilih Site", site_list, default=site_list if site_list else [])

perusahaan_list = sorted(dt_timbulan["Perusahaan"].dropna().unique()) if "Perusahaan" in dt_timbulan.columns else []
perusahaan_sel = st.sidebar.multiselect("Pilih Perusahaan", perusahaan_list, default=perusahaan_list if perusahaan_list else [])

# ----- Deteksi kolom bulan-tahun di Program -----
pattern = r"^(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember) \d{4}$"
bulan_tahun_cols = [col for col in df_program.columns if re.match(pattern, str(col))]

if bulan_tahun_cols:
    df_prog_long = df_program.melt(
        id_vars=[c for c in df_program.columns if c not in bulan_tahun_cols],
        value_vars=bulan_tahun_cols,
        var_name="Bulan-Tahun",
        value_name="Value"
    )
    df_prog_long["Tahun"] = df_prog_long["Bulan-Tahun"].apply(lambda x: int(x.split(" ")[1]))
    df_prog_long["Bulan"] = df_prog_long["Bulan-Tahun"].apply(lambda x: x.split(" ")[0])
else:
    df_prog_long = pd.DataFrame(columns=["Tahun", "Bulan", "Value"])

bulan_map = {
    "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
    "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
    "September": 9, "Oktober": 10, "November": 11, "Desember": 12
}

if not df_prog_long.empty:
    df_prog_long["Periode"] = df_prog_long.apply(
        lambda row: datetime.datetime(row["Tahun"], bulan_map[row["Bulan"]], 1),
        axis=1
    )

# ----- Tambah Tahun di Ketidaksesuaian (kalau ada) -----
if not df_ketidaksesuaian.empty and "TanggalLapor" in df_ketidaksesuaian.columns:
    df_ketidaksesuaian["TanggalLapor"] = pd.to_datetime(
        df_ketidaksesuaian["TanggalLapor"], dayfirst=True, errors="coerce"
    )
    df_ketidaksesuaian["Tahun"] = df_ketidaksesuaian["TanggalLapor"].dt.year
    df_ketidaksesuaian["Bulan"] = df_ketidaksesuaian["TanggalLapor"].dt.month

# -------------------------
# 🔹 FILTER TAHUN
# -------------------------
tahun_tersedia = sorted(df_prog_long["Tahun"].dropna().astype(int).unique().tolist()) if "Tahun" in df_prog_long.columns else []
if "Tahun" in dt_timbulan.columns:
    tahun_tersedia = sorted(
        set(tahun_tersedia) | set(dt_timbulan["Tahun"].dropna().astype(int).unique().tolist())
    )

tahun_pilihan = st.sidebar.multiselect(
    "Pilih Tahun:", tahun_tersedia, default=tahun_tersedia
)

# Untuk hitung rata-rata per hari (approx.)
if tahun_pilihan:
    days_period = 365 * len(tahun_pilihan)
else:
    days_period = 365

# -------------------------
# 🔹 APPLY FILTER TAHUN KE SEMUA DF
# -------------------------
if tahun_pilihan:
    if "Tahun" in dt_timbulan.columns:
        dt_timbulan = dt_timbulan[dt_timbulan["Tahun"].isin(tahun_pilihan)]

    if "Tahun" in dt_program.columns:
        dt_program = dt_program[dt_program["Tahun"].isin(tahun_pilihan)]

    if not df_ketidaksesuaian.empty and "Tahun" in df_ketidaksesuaian.columns:
        df_ketidaksesuaian = df_ketidaksesuaian[df_ketidaksesuaian["Tahun"].isin(tahun_pilihan)]

    if not dt_online.empty and "Tanggal" in dt_online.columns:
        dt_online["Tanggal"] = pd.to_datetime(dt_online["Tanggal"], dayfirst=True, errors="coerce")
        dt_online["Tahun"] = dt_online["Tanggal"].dt.year
        dt_online = dt_online[dt_online["Tahun"].isin(tahun_pilihan)]

# -------------------------
# 🔹 FILTER SITE & PERUSAHAAN
# -------------------------
df_timbulan_filtered = dt_timbulan.copy()
if site_sel:
    df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["Site"].isin(site_sel)]
if perusahaan_sel:
    df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["Perusahaan"].isin(perusahaan_sel)]

df_program_filtered = dt_program.copy()
if site_sel and "Site" in df_program_filtered.columns:
    df_program_filtered = df_program_filtered[df_program_filtered["Site"].isin(site_sel)]
if perusahaan_sel and "Perusahaan" in df_program_filtered.columns:
    df_program_filtered = df_program_filtered[df_program_filtered["Perusahaan"].isin(perusahaan_sel)]

df_ket_filtered = df_ketidaksesuaian.copy()
if site_sel and "Site" in df_ket_filtered.columns:
    df_ket_filtered = df_ket_filtered[df_ket_filtered["Site"].isin(site_sel)]
if perusahaan_sel and "Perusahaan" in df_ket_filtered.columns:
    df_ket_filtered = df_ket_filtered[df_ket_filtered["Perusahaan"].isin(perusahaan_sel)]

# =============================
# METRIC UTAMA (atas)
# =============================
try:
    df_timbulan = df_timbulan_filtered.copy()
    df_program = df_program_filtered.copy()
    df_ket = df_ket_filtered.copy()

    # --- Total Timbulan ---
    if "Timbulan" in df_timbulan.columns:
        df_timbulan["Timbulan"] = pd.to_numeric(
            df_timbulan["Timbulan"].astype(str).str.replace(",", "."),
            errors="coerce"
        )

        total_timbulan = df_timbulan["Timbulan"].sum()

        # kalau ada kolom data_input_total dipakai, kalau tidak pakai total_timbulan
        if "data_input_total" in df_timbulan.columns:
            total_timbulan_all = pd.to_numeric(
                df_timbulan["data_input_total"], errors="coerce"
            ).sum()
        else:
            total_timbulan_all = total_timbulan
    else:
        total_timbulan = 0
        total_timbulan_all = 0

    # --- Man Power unik & jumlah unit perusahaan-site (LOGIKA SAMA DENGAN SNI) ---
    if not df_timbulan.empty and {"Site", "Perusahaan", "Man Power"}.issubset(df_timbulan.columns):
        subset_cols = ["Site", "Perusahaan"]
        if "Tahun" in df_timbulan.columns:
            subset_cols.append("Tahun")

        df_mp_unik_metric = (
            df_timbulan
            .drop_duplicates(subset=subset_cols, keep="last")
            [subset_cols + ["Man Power"]]
            .copy()
        )

        df_mp_unik_metric["Man Power"] = pd.to_numeric(
            df_mp_unik_metric["Man Power"], errors="coerce"
        ).fillna(0)

        total_manpower = df_mp_unik_metric["Man Power"].sum()
        jumlah_unit = (
                df_mp_unik_metric[["Site", "Perusahaan"]]
                .drop_duplicates()
                .shape[0]
        )
    else:
        total_manpower = 0
        jumlah_unit = 0

    rasio_manpower = total_timbulan / total_manpower if total_manpower > 0 else 0

    # --- Jumlah Program ---
    if "Nama program" in df_program.columns:
        df_program["Total_calc"] = pd.to_numeric(
            df_program["Total_calc"].astype(str).str.replace(",", "."),
            errors="coerce"
        )
        jumlah_program = df_program["Nama program"].dropna().shape[0]
        total_program = df_program["Total_calc"].sum()
    else:
        jumlah_program = 0
        total_program = 0

    # --- Ketidaksesuaian Valid ---
    if "status_temuan" in df_ket.columns:
        total_ketidaksesuaian = df_ket.query("status_temuan == 'Valid'").shape[0]
        temuan_masuk = df_ket["status_temuan"].count()
    else:
        total_ketidaksesuaian = 0
        temuan_masuk = 0

    # --- Persentase program terkelola (approx) ---
    if total_timbulan > 0 and total_program > 0 and days_period > 0:
        avg_timbulan_perhari = total_timbulan
        avg_program_perhari = total_program / days_period
        persentase_terkelola = (avg_program_perhari / avg_timbulan_perhari) * 100
    else:
        persentase_terkelola = 0

    # ---------- STYLE CARD ----------
    card_style = """
        background-color:#ffffff;
        border-radius:10px;
        padding:14px 16px;
        box-shadow:0 2px 4px rgba(15,15,15,0.08);
    """

    # ---------- TAMPILKAN 3 CARD METRIK ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
            <div style="{card_style}">
                <h6 style="margin-bottom:4px;margin-top:0;font-weight:normal;">Total Timbulan (kg)</h6>
                <p style="font-size:40px; margin:0;">{total_timbulan_all:,.0f}</p>
                <p style="font-size:13px; margin-top:4px; color:#3BB143;">
                    per {jumlah_unit} perusahaan-site dari <strong>{total_manpower:,.0f}</strong> manpower unik
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="{card_style}">
                <h6 style="margin-bottom:4px;margin-top:0;font-weight:normal;">Rata-rata Timbulan (kg/hari)</h6>
                <p style="font-size:40px; margin:0;">{total_timbulan:.2f}</p>
                <p style="font-size:13px; margin-top:4px; color:#3BB143;">
                    dengan <strong>{rasio_manpower:.2f}</strong> kg/hari/manpower
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="{card_style}">
                <h6 style="margin-bottom:4px;margin-top:0;font-weight:normal;">Jumlah Man Power (Unik)</h6>
                <p style="font-size:40px; margin:0;">{total_manpower:,.0f}</p>
                <p style="font-size:13px; margin-top:4px; color:#3BB143;">
                    pada {jumlah_unit} perusahaan-site terpilih
                </p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error("Gagal menghitung metric.")
    st.exception(e)


 # ======================================================
# 🔢 RATA-RATA TIMBULAN SESUAI SNI (kg/hari/orang)
# ======================================================
st.markdown("### ♻️ Rata-rata Timbulan Sesuai SNI (kg/hari/orang)")

if not df_timbulan.empty and {"Site", "Perusahaan", "Timbulan", "Man Power"}.issubset(df_timbulan.columns):
    df_timbulan_sni = df_timbulan.copy()
    df_timbulan_sni["Timbulan"] = pd.to_numeric(df_timbulan_sni["Timbulan"], errors="coerce").fillna(0)
    df_timbulan_sni["Man Power"] = pd.to_numeric(df_timbulan_sni["Man Power"], errors="coerce").fillna(0)

    # kombinasi unik site-perusahaan-tahun (kalau kolom Tahun ada)
    subset_cols_sni = ["Site", "Perusahaan"]
    if "Tahun" in df_timbulan_sni.columns:
        subset_cols_sni.append("Tahun")

    df_mp_unik_sni = (
        df_timbulan_sni
        .drop_duplicates(subset=subset_cols_sni, keep="last")
        [subset_cols_sni + ["Man Power"]]
        .copy()
    )

    df_mp_unik_sni["Man Power"] = pd.to_numeric(
        df_mp_unik_sni["Man Power"], errors="coerce"
    ).fillna(0)

    total_timbulan_all_sni = df_timbulan_sni["Timbulan"].sum()
    total_mp_unik = df_mp_unik_sni["Man Power"].sum()   # → harusnya jadi 3.498


    rata_sni = total_timbulan_all_sni / total_mp_unik if total_mp_unik > 0 else 0

    st.markdown(f"""
    <div style="background:#f8fff5;border:1px solid #a5d6a7;border-radius:8px;padding:15px;margin-bottom:10px;">
        <h5 style="margin:0;color:#2e7d32;">Rata-rata Timbulan (SNI)</h5>
        <p style="font-size:32px;margin:0;color:#1b5e20;"><strong>{rata_sni:.3f}</strong> kg/hari/orang</p>
        <p style="font-size:13px;margin-top:4px;color:#388e3c;">
            Total Timbulan: {total_timbulan_all_sni:,.0f} kg | Total Man Power Unik: {total_mp_unik:,.0f}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📋 Rincian per Site")
    df_site_sni = (
        df_timbulan_sni.groupby("Site", as_index=False)
        .agg(total_timbulan=("Timbulan", "sum"))
        .merge(
            df_mp_unik_sni.groupby("Site", as_index=False)["Man Power"].sum(),
            on="Site", how="left"
        )
    )
    df_site_sni["kg/hari/orang"] = (
        df_site_sni["total_timbulan"] / df_site_sni["Man Power"]
    ).round(3)
    df_site_sni = df_site_sni.sort_values("kg/hari/orang", ascending=False)
    st.dataframe(df_site_sni, hide_index=True)
else:
    st.warning("Kolom 'Timbulan', 'Man Power', 'Site', atau 'Perusahaan' belum lengkap untuk perhitungan SNI.")


# =============================
# TOTAL TIMBULAN PER SITE/PERUSAHAAN
# =============================
total_timbulan = df_timbulan_filtered["Timbulan"].sum()
jumlah_program = dt_program.shape[0]
avg_perhari = dt_program["Total_calc"].sum() / days_period if days_period > 0 else 0

with st.container():
    col1, col2 = st.columns([0.5, 0.5])

    # --- Total Timbulan per Site ---
    with col1:
        st.markdown('<p style="text-align: center;font-weight: bold;">📊 Total Timbulan per Site</p>',
                    unsafe_allow_html=True)
        if not df_timbulan_filtered.empty:
            total_site_timbulan = df_timbulan_filtered.groupby("Site", as_index=False)["Timbulan"].sum()
            manpower_unique = df_timbulan_filtered[["Site", "Perusahaan", "Man Power"]].drop_duplicates()
            manpower_site = manpower_unique.groupby("Site", as_index=False)["Man Power"].sum()
            total_site = total_site_timbulan.merge(manpower_site, on="Site", how="left")

            fig1 = px.bar(
                total_site,
                x="Site",
                y="Timbulan",
                text="Timbulan",
                color="Timbulan",
                color_continuous_scale=["#b7e4c7", "#52b788", "#1b4332"],
                labels={"Timbulan": "Total Timbulan (kg)"},
                template="plotly_white"
            )
            fig1.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
                hovertemplate="<b>Site:</b> %{x}<br>"
                              "<b>Total Timbulan:</b> %{y:,.0f} kg<br>"
                              "<b>Man Power:</b> %{customdata[0]:,.0f}<br><extra></extra>",
                customdata=total_site[["Man Power"]].values
            )
            fig1.update_layout(height=400, width=800, margin=dict(t=50, b=100))
            st.plotly_chart(fig1, use_container_width=True)

    # --- Timbulan per Perusahaan-Site ---
    with col2:
        st.markdown('<p style="text-align: center;font-weight: bold;">📊 Timbulan per Perusahaan - Site</p>',
                    unsafe_allow_html=True)
        if not df_timbulan_filtered.empty and "Perusahaan" in df_timbulan_filtered.columns:
            total_perusahaan = df_timbulan_filtered.groupby(
                ["Perusahaan", "Site"], as_index=False
            )["Timbulan"].sum()
            total_perusahaan["Perusahaan_Site"] = total_perusahaan["Perusahaan"] + " - " + total_perusahaan["Site"]

            manpower_unique = df_timbulan_filtered[["Site", "Perusahaan", "Man Power"]].drop_duplicates()
            manpower_site_mitra = manpower_unique.groupby(
                ["Site", "Perusahaan"], as_index=False
            )["Man Power"].sum()

            total_manpower_perusahaan = total_perusahaan.merge(
                manpower_site_mitra, on=["Site", "Perusahaan"], how="left"
            )

            fig1b = px.bar(
                total_perusahaan,
                y="Perusahaan_Site",
                x="Timbulan",
                text="Timbulan",
                color="Timbulan",
                color_continuous_scale=["#b7e4c7", "#52b788", "#1b4332"],
                labels={"Timbulan": "Total Timbulan (kg)", "Perusahaan_Site": "Perusahaan - Site"},
                template="plotly_white",
                orientation="h"
            )
            fig1b.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
                hovertemplate="<b>Total Timbulan:</b> %{x:,.0f} kg<br>"
                              "<b>Man Power:</b> %{customdata[1]:,.0f}<br><extra></extra>",
                customdata=total_manpower_perusahaan[["Perusahaan", "Man Power"]].values
            )
            fig1b.update_layout(
                height=400,
                width=800,
                margin=dict(t=50, b=50),
                yaxis=dict(autorange="reversed"),
                coloraxis_colorbar=dict(
                    title=dict(text="Total Timbulan (kg/hari)", side="right", font=dict(size=10)),
                    tickfont=dict(size=9),
                    thickness=12,
                    len=0.6,
                    x=1.05
                )
            )
            st.plotly_chart(fig1b, use_container_width=True)

# ===========================
# FILTER ORGANIK / ANORGANIK
# ===========================
st.markdown('<p style="text-align:center;font-weight: bold;">🗑️ Filter Jenis Sampah</p>', unsafe_allow_html=True)

jenis_pilihan = (
    df_timbulan_filtered["jenis_sampah"].dropna().unique().tolist()
    if "jenis_sampah" in df_timbulan_filtered.columns else []
)

cl1, cl2 = st.columns(2)
with cl1:
    pilih_organik = st.checkbox("Organik", value=True)
with cl2:
    pilih_anorganik = st.checkbox("Anorganik", value=True)

df_filterjensampah = df_timbulan_filtered[df_timbulan_filtered["jenis_sampah"].isin(jenis_pilihan)]

if pilih_organik and not pilih_anorganik:
    df_filterjensampah = df_timbulan_filtered[df_timbulan_filtered["jenis_sampah"] == "Organik"]
elif pilih_anorganik and not pilih_organik:
    df_filterjensampah = df_timbulan_filtered[df_timbulan_filtered["jenis_sampah"] == "Anorganik"]
elif not (pilih_organik or pilih_anorganik):
    df_filterjensampah = pd.DataFrame(columns=df_timbulan_filtered.columns)
else:
    df_filterjensampah = df_timbulan_filtered

if not df_timbulan_filtered.empty and "jenis_timbulan" in df_timbulan_filtered.columns:
    jenis_unique = df_timbulan_filtered["jenis_timbulan"].unique()
    colors = px.colors.sequential.Viridis[:len(jenis_unique)]
    color_map = {j: c for j, c in zip(jenis_unique, colors)}

    col1, col2 = st.columns([0.35, 0.65])

    # Pie Organik vs Anorganik
    with col1:
        st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Sampah Organik vs Anorganik</p>',
                    unsafe_allow_html=True)
        proporsi = df_filterjensampah.groupby("jenis_sampah", as_index=False)["Timbulan"].sum()
        fig1 = px.pie(
            proporsi,
            names="jenis_sampah",
            values="Timbulan",
            hole=0.4,
            color="jenis_sampah",
            color_discrete_map={"Organik": "#1a5b1d", "Anorganik": "#d3d30e"}
        )
        fig1.update_traces(textinfo="percent+label", pull=[0.01] * len(proporsi))
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    # Bar per Perusahaan-Site (Organik/Anorganik)
    with col2:
        st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Timbulan per Perusahaan - Site</p>',
                    unsafe_allow_html=True)
        if not df_filterjensampah.empty and "Perusahaan" in df_filterjensampah.columns:
            total_perusahaan = df_filterjensampah.groupby(
                ["Perusahaan", "Site", "jenis_sampah"], as_index=False
            )["Timbulan"].sum()
            total_perusahaan["Perusahaan_Site"] = total_perusahaan["Perusahaan"] + " - " + total_perusahaan["Site"]

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
                barmode="stack",
                bargap=0.2,
                legend=dict(
                    orientation="h", font=dict(size=8),
                    yanchor="top", y=1.2,
                    x=0.2, xanchor="center",
                    traceorder="normal", valign="top"
                )
            )
            st.plotly_chart(fig3, use_container_width=True)

    # Detail jenis timbulan
    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.markdown('<p style="text-align: left;font-weight: bold;">🔎 Proporsi Detail per Jenis Timbulan</p>',
                    unsafe_allow_html=True)
        jenis_detail = df_filterjensampah.groupby("jenis_timbulan", as_index=False)["Timbulan"].sum()
        fig2 = px.pie(
            jenis_detail,
            names="jenis_timbulan",
            values="Timbulan",
            color="jenis_timbulan",
            hole=0.3,
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig2.update_traces(textinfo="percent+label", pull=[0.01] * len(jenis_detail))
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Detail Timbulan per Perusahaan - Site</p>',
                    unsafe_allow_html=True)
        if not df_filterjensampah.empty and "Perusahaan" in df_filterjensampah.columns:
            total_perusahaan_detail = df_filterjensampah.groupby(
                ["Perusahaan", "Site", "jenis_timbulan"], as_index=False
            )["Timbulan"].sum()
            total_perusahaan_detail["Perusahaan_Site"] = (
                total_perusahaan_detail["Perusahaan"] + " - " + total_perusahaan_detail["Site"]
            )

            fig4 = px.bar(
                total_perusahaan_detail,
                x="Perusahaan_Site",
                y="Timbulan",
                text="Timbulan",
                color="jenis_timbulan",
                color_discrete_map=color_map,
                labels={
                    "Timbulan": "Total Timbulan (kg)",
                    "Perusahaan_Site": "Perusahaan - Site",
                    "jenis_timbulan": "Jenis Timbulan"
                },
                template="plotly_white"
            )
            fig4.update_traces(texttemplate="%{text:,.0f}", textposition="inside")
            y_max = total_perusahaan_detail["Timbulan"].max()
            y_dtick = max(int(y_max / 5), 1)
            fig4.update_layout(
                height=500, width=800,
                barmode="stack",
                margin=dict(t=30, b=50, l=100, r=20),
                yaxis=dict(tickmode="linear", dtick=y_dtick),
                xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
                bargap=0.2,
                legend=dict(
                    orientation="h", font=dict(size=8),
                    yanchor="top", y=1.2,
                    x=0.8, xanchor="center",
                    traceorder="normal", valign="top"
                )
            )
            st.plotly_chart(fig4, use_container_width=True)

# ===========================
# RASIO TIMBULAN vs MANPOWER
# ===========================
if not df_timbulan_filtered.empty:
    manpower_unique = df_timbulan_filtered[["Site", "Perusahaan", "Man Power"]].drop_duplicates()
    timbulan_agg = manpower_unique.groupby(["Site", "Perusahaan"], as_index=False)["Man Power"].sum()
    timbulan_site_perusahaan = df_timbulan_filtered.groupby(
        ["Site", "Perusahaan"], as_index=False
    )["Timbulan"].sum()

    df_agg = timbulan_site_perusahaan.merge(
        timbulan_agg, on=["Perusahaan", "Site"], how="left"
    )
    df_agg["Rasio_Timbulan"] = df_agg["Timbulan"] / df_agg["Man Power"]

    mean_ratio = df_agg["Rasio_Timbulan"].mean()
    std_ratio = df_agg["Rasio_Timbulan"].std()
    df_agg["Zscore"] = (df_agg["Rasio_Timbulan"] - mean_ratio) / std_ratio

    def kategori_iqr(r):
        Q1 = df_agg["Rasio_Timbulan"].quantile(0.25)
        Q3 = df_agg["Rasio_Timbulan"].quantile(0.75)
        IQR = Q3 - Q1
        if r <= Q3:
            return "Normal"
        elif Q1 - 1.5 * IQR <= r < Q1 or Q3 < r <= Q3 + 1.5 * IQR:
            return "Siaga"
        else:
            return "Tidak Normal"

    df_agg["Kategori"] = df_agg["Rasio_Timbulan"].apply(kategori_iqr)
    df_agg["Perusahaan_Site"] = df_agg["Perusahaan"] + " - " + df_agg["Site"]

    color_map_ratio = {
        "Normal": "#1a9850",
        "Siaga": "#fee08b",
        "Tidak Normal": "#d73027"
    }

    Q1 = df_agg["Rasio_Timbulan"].quantile(0.25)
    Q3 = df_agg["Rasio_Timbulan"].quantile(0.75)
    IQR = Q3 - Q1

    col1, col2 = st.columns([0.65, 0.35])
    with col1:
        st.markdown('<p style="text-align: left;font-weight: bold;">⚖️ Rasio Timbulan/Manpower</p>',
                    unsafe_allow_html=True)
        fig = px.bar(
            df_agg,
            x="Perusahaan_Site",
            y="Rasio_Timbulan",
            color="Kategori",
            color_discrete_map=color_map_ratio,
            text=df_agg["Rasio_Timbulan"].round(2),
            labels={"Rasio_Timbulan": "Rasio Timbulan per Manpower (kg/orang)"},
            template="plotly_white"
        )
        fig.add_hline(y=Q1, line_dash="dot", line_color="green",
                      annotation_text=f"Q1 = {Q1:.2f}", annotation_position="bottom left")
        fig.add_hline(y=Q3, line_dash="dot", line_color="green",
                      annotation_text=f"Q3 = {Q3:.2f}", annotation_position="top left")
        fig.add_hline(y=Q3 + 1.5 * IQR, line_dash="dash", line_color="orange",
                      annotation_text=f"Batas Siaga = {Q3 + 1.5 * IQR:.2f}", annotation_position="top right")

        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis=dict(tickangle=-30),
            margin=dict(t=40, b=120, l=50, r=50),
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p style="text-align: left;font-weight: bold;">📦 Distribusi Z-score Rasio Timbulan/Manpower</p>',
                    unsafe_allow_html=True)
        fig_box = px.box(
            df_agg,
            y="Zscore",
            points="all",
            hover_data=["Perusahaan_Site", "Rasio_Timbulan"],
            labels={"Zscore": "Z-score Rasio Timbulan"},
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

    with st.expander("Detail Data Rasio Timbulan per Manpower"):
        st.dataframe(df_agg[["Perusahaan_Site", "Timbulan", "Man Power",
                             "Rasio_Timbulan", "Zscore", "Kategori"]])

# ===========================
# VOLUME vs KAPASITAS & CCTV
# ===========================
df_filtered = df_filterjensampah.copy()

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

if not df_filtered.empty:
    df_filtered["rho"] = df_filtered["jenis_timbulan"].map(rho_map)
    df_filtered["Timbulan_Volume"] = df_filtered["Timbulan"] / df_filtered["rho"]

    organik_list = ["Organik", "Organik Lainnya", "Sisa Makanan & Sayur"]
    anorganik_list = ["Kardus", "Botol Plastik", "Plastik", "Kertas", "Lainnya"]

    df_grouped = df_filtered.groupby(
        ["Site", "Perusahaan", "jenis_timbulan", "jenis_sampah", "Kapasitas", "Kapasitas.1"],
        as_index=False
    ).agg({"Timbulan_Volume": "sum"})

    df_grouped["Timbulan_Organik_Volume"] = np.where(
        df_grouped["jenis_timbulan"].isin(organik_list),
        df_grouped["Timbulan_Volume"], 0
    )
    df_grouped["Timbulan_Anorganik_Volume"] = np.where(
        df_grouped["jenis_timbulan"].isin(anorganik_list),
        df_grouped["Timbulan_Volume"], 0
    )

    df_pivot = df_grouped.groupby(["Site", "Perusahaan"], as_index=False).agg({
        "Timbulan_Organik_Volume": "sum",
        "Timbulan_Anorganik_Volume": "sum",
        "Kapasitas": "max",
        "Kapasitas.1": "max"
    }).rename(columns={"Kapasitas": "Kapasitas_Organik", "Kapasitas.1": "Kapasitas_Anorganik"})

    def kategori_icon(timbulan, kapasitas):
        if kapasitas == 0 or pd.isna(kapasitas):
            return "❓"
        if timbulan < 0.7 * kapasitas:
            return "✅"
        elif timbulan <= kapasitas:
            return "⚠️"
        else:
            return "❌"

    df_pivot["Status_Organik"] = df_pivot.apply(
        lambda r: kategori_icon(r["Timbulan_Organik_Volume"], r["Kapasitas_Organik"]), axis=1
    )
    df_pivot["Status_Anorganik"] = df_pivot.apply(
        lambda r: kategori_icon(r["Timbulan_Anorganik_Volume"], r["Kapasitas_Anorganik"]), axis=1
    )

    text_organik = df_pivot["Timbulan_Organik_Volume"].round(1).astype(str) + " L | " + df_pivot["Status_Organik"]
    text_anorganik = df_pivot["Timbulan_Anorganik_Volume"].round(1).astype(str) + " L | " + df_pivot["Status_Anorganik"]

    df_pivot["Perusahaan_Site"] = df_pivot["Perusahaan"] + "-" + df_pivot["Site"]
    perusahaan_list = df_pivot["Perusahaan_Site"]

    col1, col2 = st.columns([0.65, 0.35])
    with col1:
        st.markdown('<p style="text-align: left;font-weight: bold;">⚖️ Timbulan vs Kapasitas Tempat Sampah</p>',
                    unsafe_allow_html=True)
        color_map_vs = {"Organik": "#1a5b1d", "Anorganik": "#d3d30e"}

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot["Kapasitas_Anorganik"],
            name="Kapasitas Anorganik",
            orientation="h",
            marker_color=color_map_vs["Anorganik"],
            opacity=0.2,
            text=text_anorganik,
            textposition="outside",
            width=0.4,
            offset=-0.2
        ))
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot["Kapasitas_Organik"],
            name="Kapasitas Organik",
            orientation="h",
            marker_color=color_map_vs["Organik"],
            opacity=0.2,
            text=text_organik,
            textposition="outside",
            width=0.4,
            offset=0.2
        ))
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot["Timbulan_Anorganik_Volume"],
            name="Timbulan Anorganik",
            orientation="h",
            marker_color=color_map_vs["Anorganik"],
            width=0.4,
            offset=-0.2
        ))
        fig.add_trace(go.Bar(
            y=perusahaan_list,
            x=df_pivot["Timbulan_Organik_Volume"],
            name="Timbulan Organik",
            orientation="h",
            marker_color=color_map_vs["Organik"],
            width=0.4,
            offset=0.2
        ))

        fig.update_layout(
            barmode="overlay",
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

    # ----- CCTV per Perusahaan-Site -----
    if not df_cctv.empty and {"Site", "Perusahaan", "Coverage 24jam",
                              "Coverage non 24jam", "Tidak tercover", "Total CCTV"}.issubset(df_cctv.columns):
        df_cctv_filtered = df_cctv.copy()
        if site_sel:
            df_cctv_filtered = df_cctv_filtered[df_cctv_filtered["Site"].isin(site_sel)]
        if perusahaan_sel:
            df_cctv_filtered = df_cctv_filtered[df_cctv_filtered["Perusahaan"].isin(perusahaan_sel)]

        df_cctv_filtered["Perusahaan_Site"] = df_cctv_filtered["Perusahaan"] + "-" + df_cctv_filtered["Site"]

        with col2:
            st.markdown('<p style="text-align: left;font-weight: bold;">📊 Visualisasi CCTV per Perusahaan-Site</p>',
                        unsafe_allow_html=True)
            fig_c = go.Figure()
            for _, row in df_cctv_filtered.iterrows():
                fig_c.add_trace(go.Bar(
                    x=[row["Coverage 24jam"], row["Coverage non 24jam"], row["Tidak tercover"]],
                    y=[row["Perusahaan_Site"], row["Perusahaan_Site"], row["Perusahaan_Site"]],
                    orientation="h",
                    text=[row["Coverage 24jam"], row["Coverage non 24jam"], row["Tidak tercover"]],
                    showlegend=False,
                    marker=dict(color=["#1a9850", "#fee08b", "#d73027"])
                ))

            fig_c.update_layout(
                barmode="stack",
                xaxis_title="Jumlah CCTV",
                yaxis_title="Perusahaan-Site",
                showlegend=False
            )
            st.plotly_chart(fig_c, use_container_width=True)

    with st.expander("Detail Timbulan & Kapasitas per Perusahaan-Site"):
        st.dataframe(df_pivot)
