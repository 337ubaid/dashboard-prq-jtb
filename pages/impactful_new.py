import importlib
from typing import Any
import pandas as pd
import streamlit as st

import utils.data_processing
import utils.helpers

# Force reload utility modules to prevent cached imports on running Streamlit server
importlib.reload(utils.helpers)
importlib.reload(utils.data_processing)

from utils.data_processing import (
    METRICS_MAPPING,
    load_and_clean_monthly_data,
    load_monthly_impactful_data,
    TELDA_REGIONS,
)
from utils.helpers import setup_page

# ==========================================
# Named Constants & Configuration (G25, P2)
# ==========================================
LTS_TARGET: float = 56.0
C3MR_TARGET: float = 98.0
ACHIEVEMENT_CAP: float = 110.0

ACH_EXCELLENT_THRESHOLD: float = 100.0
ACH_GOOD_THRESHOLD: float = 90.0

QUARTER_MONTHS_MAPPING: dict[str, list[str]] = {
    "Q1": ["202601", "202602", "202603"],
    "Q2": ["202604", "202605", "202606"],
    "Q3": ["202607", "202608", "202609"],
    "Q4": ["202610", "202611", "202612"],
}

SCORECARD_METRICS: list[dict[str, Any]] = [
    {"display": "REVENUE BS POTS", "col": "REV SME - POTS", "weight": 35.0},
    {"display": "REVENUE BS NON POTS", "col": "REV SME - NON POTS", "weight": 5.0},
    {"display": "REVENUE GS", "col": "REV GOV", "weight": 5.0},
    {"display": "REVENUE PS", "col": "REV PS", "weight": 5.0},
    {"display": "REVENUE SS", "col": "REV SOE", "weight": 5.0},
    {"display": "C3MR", "col": "C3MR", "weight": 5.0},
    {"display": "HSI_WMS", "col": "TABEL HSI + TABEL WMS", "weight": 20.0},
    {"display": "BW", "col": "BW", "weight": 5.0},
    {"display": "OCA", "col": "OCA", "weight": 2.0},
    {"display": "NETMONK", "col": "NETMONK", "weight": 3.0},
    {"display": "EAZY", "col": "EAZY", "weight": 3.0},
    {"display": "PIJAR", "col": "PIJAR SEKOLAH", "weight": 2.0},
    {"display": "LTS", "col": "LTS", "weight": 3.0},
    {"display": "VISIT_PROFILING", "col": "TABEL VISIT & PROFILING", "weight": 2.0},
]


def render_header() -> None:
    """Renders the dashboard page title and subtitle."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #1e3a8a; font-weight: 800; font-size: 32px; margin-bottom: 4px;">⚙️ Monthly Impactful Data Pipeline</h1>
            <p style="color: #64748b; font-size: 14px; margin-top: 0;">Prototype Pengolahan Data: Proses Ekstraksi (Splitting) & Konsolidasi Grid Spreadsheet (T.B. 2026)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_collect_tab(df_raw: pd.DataFrame) -> None:
    """Renders raw spreadsheet grid data with its download utility."""
    st.subheader("1. Literal Raw Spreadsheet Grid")
    st.markdown(
        "Berikut adalah grid 2D asli (list of lists) tepat setelah dibaca "
        "dari Google Sheets tab **'Impactful Telda New'** sebelum diproses."
    )

    st.info(f"Dimensi Grid Mentah: {df_raw.shape[0]} Baris × {df_raw.shape[1]} Kolom")
    st.dataframe(df_raw, use_container_width=True)

    csv_raw = df_raw.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Grid Mentah Sebagai CSV",
        data=csv_raw,
        file_name="literal_raw_spreadsheet_grid.csv",
        mime="text/csv",
        help="Klik untuk mengunduh grid data mentah dalam format CSV.",
    )


def render_split_tab(df_consolidated: pd.DataFrame) -> None:
    """Renders extracted individual metric tables selected from a dropdown list."""
    st.subheader("2. Splitting Individual Tables")
    st.markdown(
        "Spreadsheet mentah berisi **17 tabel independen** yang terfragmentasi secara vertikal. "
        "Gunakan dropdown di bawah untuk melihat hasil ekstraksi Target & Realisasi dari masing-masing tabel."
    )

    metric_options = [f"Tabel {i}: {METRICS_MAPPING[i]}" for i in range(1, 17)]
    selected_option = st.selectbox(
        "Pilih Tabel / Metrik Untuk Ditinjau:", options=metric_options, index=0
    )

    selected_idx = int(selected_option.split(":")[0].replace("Tabel ", "").strip())
    metric_name = METRICS_MAPPING[selected_idx]

    st.success(f"Menampilkan hasil ekstraksi untuk **{metric_name}**")

    metric_cols = ["TELDA", "MONTH"]
    if f"{metric_name} - TARGET" in df_consolidated.columns:
        metric_cols.append(f"{metric_name} - TARGET")
    metric_cols.append(f"{metric_name} - REALIASASI")

    df_metric_split = df_consolidated[metric_cols].copy().sort_values(by=["MONTH", "TELDA"])

    format_split = {
        c: "{:,.2f}" for c in df_metric_split.columns if c not in ["TELDA", "MONTH"]
    }
    st.dataframe(df_metric_split.style.format(format_split), use_container_width=True)

    csv_split = df_metric_split.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Unduh Tabel {metric_name} Sebagai CSV",
        data=csv_split,
        file_name=f"split_table_{metric_name.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )


def render_merge_tab(df_consolidated: pd.DataFrame) -> None:
    """Renders consolidated unified monthly database."""
    st.subheader("3. Consolidated Raw Merged Database")
    st.markdown(
        "Berikut adalah seluruh database bulanan hasil konsolidasi murni tanpa modifikasi pencapaian atau filter. "
        "Setiap baris merupakan rekaman tunggal unik berdasarkan kombinasi **TELDA** dan **MONTH**."
    )

    df_sorted_consolidated = df_consolidated.copy().sort_values(by=["MONTH", "TELDA"])

    front_cols = ["TELDA", "MONTH"]
    other_cols = [c for c in df_sorted_consolidated.columns if c not in front_cols]
    df_sorted_consolidated = df_sorted_consolidated[front_cols + other_cols]

    st.info(
        f"Dimensi Unified Database: {df_sorted_consolidated.shape[0]} Baris × {df_sorted_consolidated.shape[1]} Kolom"
    )

    format_dict = {c: "{:,.2f}" for c in other_cols}
    st.dataframe(
        df_sorted_consolidated.style.format(format_dict), use_container_width=True
    )

    csv_consolidated = df_sorted_consolidated.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Unified Database Sebagai CSV",
        data=csv_consolidated,
        file_name="consolidated_monthly_impactful_data.csv",
        mime="text/csv",
        help="Klik untuk mengunduh seluruh database gabungan dalam format CSV.",
    )


def compute_scorecard_for_subset(df_subset: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Computes scorecard targets, realizations, achievements and scores for a specific DataFrame subset (G30, G5)."""
    result = {}

    do_cto_real_sum = df_subset["DO CTO - REALIASASI"].sum() if not df_subset.empty else 0.0
    real_sales_real_sum = df_subset["REAL SALES - REALIASASI"].sum() if not df_subset.empty else 0.0
    c3mr_bayar_real_sum = df_subset["C3MR BAYAR - REALIASASI"].sum() if not df_subset.empty else 0.0
    c3mr_bill_real_sum = df_subset["C3MR BILL - REALIASASI"].sum() if not df_subset.empty else 0.0

    for item in SCORECARD_METRICS:
        display_name = item["display"]
        col_name = item["col"]
        bobot = item["weight"]

        target_sum = 0.0
        real_sum = 0.0
        ach_val = 0.0

        if df_subset.empty:
            if display_name == "LTS":
                target_sum = LTS_TARGET
                real_sum = 0.0
                ach_val = 100.0
            elif display_name == "C3MR":
                target_sum = C3MR_TARGET
                real_sum = 0.0
                ach_val = 0.0
            else:
                target_sum = 0.0
                real_sum = 0.0
                ach_val = 0.0
        else:
            if display_name == "LTS":
                target_sum = LTS_TARGET
                real_sum = (
                    (do_cto_real_sum / real_sales_real_sum * 100)
                    if real_sales_real_sum > 0
                    else 0.0
                )
                ach_val = (target_sum / real_sum * 100) if real_sum > 0 else 100.0
            elif display_name == "C3MR":
                target_sum = C3MR_TARGET
                real_sum = (
                    (c3mr_bayar_real_sum / c3mr_bill_real_sum * 100)
                    if c3mr_bill_real_sum > 0
                    else 0.0
                )
                ach_val = (real_sum / target_sum * 100) if target_sum > 0 else 0.0
            else:
                target_sum = df_subset[f"{col_name} - TARGET"].sum()
                real_sum = df_subset[f"{col_name} - REALIASASI"].sum()
                ach_val = (real_sum / target_sum * 100) if target_sum > 0 else 0.0

        capped_ach = min(ach_val, ACHIEVEMENT_CAP)
        point_val = (capped_ach / 100.0) * bobot

        result[display_name] = {
            "target": target_sum,
            "realisasi": real_sum,
            "ach": ach_val,
            "score": point_val,
        }

    return result


def calculate_scorecard(df_filtered: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    """Computes mathematics scorecard values (aggregate weights & points) cleanly (G30)."""
    res = compute_scorecard_for_subset(df_filtered)

    scorecard_rows = []
    total_point_sum = 0.0
    total_weight_sum = 0.0

    for item in SCORECARD_METRICS:
        display_name = item["display"]
        bobot = item["weight"]

        row_res = res[display_name]
        total_point_sum += row_res["score"]
        total_weight_sum += bobot

        scorecard_rows.append(
            {
                "Indikator": display_name,
                "Total Target": row_res["target"],
                "Total Realisasi": row_res["realisasi"],
                "Achievement (ACH)": row_res["ach"],
                "Bobot": bobot,
                "Nilai / Point": row_res["score"],
            }
        )

    return pd.DataFrame(scorecard_rows), total_weight_sum, total_point_sum


def style_ach_col(val: Any) -> str:
    """Applies conditional CSS styling on Achievement column cells."""
    if pd.isna(val) or val == "-":
        return ""
    try:
        v = float(val)
        if v >= ACH_EXCELLENT_THRESHOLD:
            return "background-color: rgba(16, 185, 129, 0.12); color: #047857; font-weight: 700;"
        if v >= ACH_GOOD_THRESHOLD:
            return "background-color: rgba(245, 158, 11, 0.12); color: #b45309; font-weight: 700;"
        return "background-color: rgba(239, 68, 68, 0.12); color: #b91c1c; font-weight: 700;"
    except ValueError:
        return ""


def compile_regional_metrics(
    df_consolidated: pd.DataFrame, 
    months: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compiles Target, Realisasi, ACH, and Score dataframes across all 8 Teldas (G5, G30)."""
    target_rows = []
    realisasi_rows = []
    ach_rows = []
    score_rows = []

    for t in TELDA_REGIONS:
        df_subset = df_consolidated[
            (df_consolidated["TELDA"] == t) & (df_consolidated["MONTH"].isin(months))
        ]
        res = compute_scorecard_for_subset(df_subset)

        row_target = {"TELDA": t}
        row_real = {"TELDA": t}
        row_ach = {"TELDA": t}
        row_score = {"TELDA": t}

        for item in SCORECARD_METRICS:
            display_name = item["display"]
            row_target[display_name] = res[display_name]["target"]
            row_real[display_name] = res[display_name]["realisasi"]
            row_ach[display_name] = res[display_name]["ach"]
            row_score[display_name] = res[display_name]["score"]

        target_rows.append(row_target)
        realisasi_rows.append(row_real)
        ach_rows.append(row_ach)
        score_rows.append(row_score)

    return (
        pd.DataFrame(target_rows),
        pd.DataFrame(realisasi_rows),
        pd.DataFrame(ach_rows),
        pd.DataFrame(score_rows),
    )


def render_styled_dataframe(
    df: pd.DataFrame, 
    is_ach: bool = False, 
    percentage_suffix: bool = False
) -> None:
    """Formats and styles dataframes for standard display in the dashboard (G30)."""
    metric_cols = [item["display"] for item in SCORECARD_METRICS]

    if is_ach:
        format_dict = {
            c: (lambda x: f"{x:,.2f}%" if pd.notna(x) else "-") for c in metric_cols
        }
        styled_df = df.style.format(format_dict).applymap(
            style_ach_col, subset=metric_cols
        )
    elif percentage_suffix:
        format_dict = {
            c: (lambda x: f"{x:,.2f}%" if pd.notna(x) else "-") for c in metric_cols
        }
        styled_df = df.style.format(format_dict)
    else:
        format_dict = {
            c: (lambda x: f"{x:,.2f}" if pd.notna(x) else "-") for c in metric_cols
        }
        styled_df = df.style.format(format_dict)

    st.dataframe(styled_df, use_container_width=True, hide_index=True)


def render_download_button(df: pd.DataFrame, filename: str, label: str) -> None:
    """Provides a unified standard CSV download button (G30)."""
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
    )


def render_filter_tab(df_consolidated: pd.DataFrame) -> None:
    """Manages simplified filters and renders QTD, MTD, and YTD analysis tables."""
    st.subheader("4. Performance & Filtering Analysis")
    st.markdown(
        "Gunakan kontrol di bawah untuk memfilter data dan melihat analisis pencapaian metrik secara akurat."
    )

    # 1. Simplified Filters
    col_telda, col_month = st.columns(2)
    with col_telda:
        all_teldas = sorted(df_consolidated["TELDA"].unique())
        selected_telda = st.selectbox(
            "Pilih Wilayah (Telda):",
            options=all_teldas,
            index=0,
            key="analysis_telda_filter",
        )

    with col_month:
        all_months = sorted(df_consolidated["MONTH"].unique())
        selected_month = st.selectbox(
            "Pilih Bulan:",
            options=all_months,
            index=len(all_months) - 1,
            key="analysis_month_filter",
        )

    if not selected_telda or not selected_month:
        st.warning("⚠️ Silakan pilih Wilayah Telda dan Bulan.")
        return

    # Filtered subset for single MTD row of chosen Telda and Month (for Scorecard Cards)
    df_filtered_single = df_consolidated[
        (df_consolidated["TELDA"] == selected_telda)
        & (df_consolidated["MONTH"] == selected_month)
    ].copy()

    if df_filtered_single.empty:
        st.warning("⚠️ Tidak ada data untuk kombinasi ini.")
        return

    # Generate old-style single scorecard metrics for visual feedback
    df_scorecard, total_weight_sum, total_point_sum = calculate_scorecard(
        df_filtered_single
    )

    st.markdown("### 🏆 Single Scorecard Summary")
    st.info(
        f"Kalkulasi ringkasan untuk Wilayah **{selected_telda}** pada Bulan **{selected_month}**."
    )

    col_weight, col_points = st.columns(2)
    with col_weight:
        st.metric(
            label="Total Bobot Metrik Aktif", value=f"{total_weight_sum:.1f}"
        )
    with col_points:
        st.metric(
            label="Total Nilai Kumulatif (Point)",
            value=f"{total_point_sum:.2f}",
            delta=f"{(total_point_sum / total_weight_sum * 100) if total_weight_sum > 0 else 0.0:.2f}% Pencapaian Indeks",
        )

    # ----------------------------------------------------
    # Table 1: QTD Table
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("### 📅 Quarter-to-Date (QTD) Scorecard")
    st.markdown(
        f"Kalkulasi kuartalan lengkap indikator untuk Wilayah **{selected_telda}** (Q1 s.d. Q4)."
    )

    q_results = {}
    for q_name, q_months in QUARTER_MONTHS_MAPPING.items():
        df_q = df_consolidated[
            (df_consolidated["TELDA"] == selected_telda)
            & (df_consolidated["MONTH"].isin(q_months))
        ]
        q_results[q_name] = compute_scorecard_for_subset(df_q)

    qtd_rows = []
    for item in SCORECARD_METRICS:
        display_name = item["display"]
        bobot = item["weight"]

        row = {
            ("Metrik / Indikator", ""): display_name,
            ("Q1", "Target"): q_results["Q1"][display_name]["target"],
            ("Q1", "Realisasi"): q_results["Q1"][display_name]["realisasi"],
            ("Q1", "ACH Asli"): q_results["Q1"][display_name]["ach"],
            ("Q1", "ACH Bobot"): q_results["Q1"][display_name]["score"],
            ("Q2", "Target"): q_results["Q2"][display_name]["target"],
            ("Q2", "Realisasi"): q_results["Q2"][display_name]["realisasi"],
            ("Q2", "ACH Asli"): q_results["Q2"][display_name]["ach"],
            ("Q2", "ACH Bobot"): q_results["Q2"][display_name]["score"],
            ("Q3", "Target"): q_results["Q3"][display_name]["target"],
            ("Q3", "Realisasi"): q_results["Q3"][display_name]["realisasi"],
            ("Q3", "ACH Asli"): q_results["Q3"][display_name]["ach"],
            ("Q3", "ACH Bobot"): q_results["Q3"][display_name]["score"],
            ("Q4", "Target"): q_results["Q4"][display_name]["target"],
            ("Q4", "Realisasi"): q_results["Q4"][display_name]["realisasi"],
            ("Q4", "ACH Asli"): q_results["Q4"][display_name]["ach"],
            ("Q4", "ACH Bobot"): q_results["Q4"][display_name]["score"],
            ("Bobot", ""): bobot,
        }
        qtd_rows.append(row)

    df_qtd = pd.DataFrame(qtd_rows)
    df_qtd.columns = pd.MultiIndex.from_tuples(df_qtd.columns)

    format_qtd = {}
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        format_qtd[(q, "Target")] = lambda x: f"{x:,.2f}" if pd.notna(x) else "-"
        format_qtd[(q, "Realisasi")] = lambda x: f"{x:,.2f}" if pd.notna(x) else "-"
        format_qtd[(q, "ACH Asli")] = lambda x: f"{x:,.2f}%" if pd.notna(x) else "-"
        format_qtd[(q, "ACH Bobot")] = lambda x: f"{x:,.2f}" if pd.notna(x) else "-"
    format_qtd[("Bobot", "")] = lambda x: f"{x:.1f}" if pd.notna(x) else "-"

    styled_qtd = df_qtd.style.format(format_qtd)
    ach_cols = [(q, "ACH Asli") for q in ["Q1", "Q2", "Q3", "Q4"]]
    styled_qtd = styled_qtd.applymap(style_ach_col, subset=ach_cols)

    st.dataframe(styled_qtd, use_container_width=True, hide_index=True)
    render_download_button(
        df_qtd,
        f"qtd_scorecard_{selected_telda.lower()}.csv",
        "📥 Unduh Tabel QTD Sebagai CSV",
    )

    # ----------------------------------------------------
    # Table 2: 4 MTD Tables
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("### 📊 Month-to-Date (MTD) Metrics (Seluruh Wilayah)")
    st.markdown(
        f"Kinerja seluruh Telda pada Bulan Terpilih **{selected_month}**."
    )

    df_mtd_t, df_mtd_r, df_mtd_a, df_mtd_s = compile_regional_metrics(
        df_consolidated, [selected_month]
    )

    tab_mtd_target, tab_mtd_real, tab_mtd_ach, tab_mtd_score = st.tabs(
        [
            "🎯 MTD Target",
            "📈 MTD Realisasi",
            "🏆 MTD Achievement (%)",
            "💰 MTD Score (Point)",
        ]
    )

    with tab_mtd_target:
        render_styled_dataframe(df_mtd_t)
        render_download_button(
            df_mtd_t, f"mtd_target_{selected_month}.csv", "📥 Unduh MTD Target Sebagai CSV"
        )
    with tab_mtd_real:
        render_styled_dataframe(df_mtd_r)
        render_download_button(
            df_mtd_r,
            f"mtd_realisasi_{selected_month}.csv",
            "📥 Unduh MTD Realisasi Sebagai CSV",
        )
    with tab_mtd_ach:
        render_styled_dataframe(df_mtd_a, is_ach=True)
        render_download_button(
            df_mtd_a,
            f"mtd_achievement_{selected_month}.csv",
            "📥 Unduh MTD Achievement Sebagai CSV",
        )
    with tab_mtd_score:
        render_styled_dataframe(df_mtd_s)
        render_download_button(
            df_mtd_s, f"mtd_score_{selected_month}.csv", "📥 Unduh MTD Score Sebagai CSV"
        )

    # ----------------------------------------------------
    # Table 3: 4 YTD Tables
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("### 📈 Year-to-Date (YTD) Metrics (Seluruh Wilayah)")
    st.markdown(
        f"Kinerja kumulatif seluruh Telda dari awal tahun s.d. Bulan Terpilih **{selected_month}**."
    )

    ytd_months = [m for m in all_months if m <= selected_month]
    df_ytd_t, df_ytd_r, df_ytd_a, df_ytd_s = compile_regional_metrics(
        df_consolidated, ytd_months
    )

    tab_ytd_target, tab_ytd_real, tab_ytd_ach, tab_ytd_score = st.tabs(
        [
            "🎯 YTD Target",
            "📈 YTD Realisasi",
            "🏆 YTD Achievement (%)",
            "💰 YTD Score (Point)",
        ]
    )

    with tab_ytd_target:
        render_styled_dataframe(df_ytd_t)
        render_download_button(
            df_ytd_t, f"ytd_target_{selected_month}.csv", "📥 Unduh YTD Target Sebagai CSV"
        )
    with tab_ytd_real:
        render_styled_dataframe(df_ytd_r)
        render_download_button(
            df_ytd_r,
            f"ytd_realisasi_{selected_month}.csv",
            "📥 Unduh YTD Realisasi Sebagai CSV",
        )
    with tab_ytd_ach:
        render_styled_dataframe(df_ytd_a, is_ach=True)
        render_download_button(
            df_ytd_a,
            f"ytd_achievement_{selected_month}.csv",
            "📥 Unduh YTD Achievement Sebagai CSV",
        )
    with tab_ytd_score:
        render_styled_dataframe(df_ytd_s)
        render_download_button(
            df_ytd_s, f"ytd_score_{selected_month}.csv", "📥 Unduh YTD Score Sebagai CSV"
        )

    # ----------------------------------------------------
    # Detailed Monthly Audit Trail (Single chosen row)
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔍 Detailed Audit Trail (Monthly Filtered Rows)")
    st.markdown(
        f"Berikut adalah data individual baris mentah terfilter untuk Wilayah **{selected_telda}** dan Bulan **{selected_month}**."
    )

    detail_format = {
        c: "{:,.2f}"
        for c in df_filtered_single.columns
        if c not in ["TELDA", "MONTH"]
    }
    st.dataframe(df_filtered_single.style.format(detail_format), use_container_width=True)


def main() -> None:
    """Main entrypoint of the streamlit pipeline dashboard page."""
    setup_page("PRQ Dashboard | Monthly Impactful Pipeline")
    render_header()

    raw_rows = load_monthly_impactful_data()
    df_consolidated = load_and_clean_monthly_data()

    # Guard Clause to prevent deep nesting (G29)
    if not raw_rows or df_consolidated.empty:
        st.warning("⚠️ Data bulanan kosong atau gagal memuat spreadsheet.")
        st.stop()

    df_raw = pd.DataFrame(raw_rows)

    tab_collect, tab_split, tab_merge, tab_filter = st.tabs(
        [
            "📥 1. Collect Raw Sheet",
            "✂️ 2. Splitting Tables",
            "🔗 3. Consolidating (Merged)",
            "📊 4. Performance & Filtering Analysis",
        ]
    )

    with tab_collect:
        render_collect_tab(df_raw)

    with tab_split:
        render_split_tab(df_consolidated)

    with tab_merge:
        render_merge_tab(df_consolidated)

    with tab_filter:
        render_filter_tab(df_consolidated)


if __name__ == "__main__":
    main()
