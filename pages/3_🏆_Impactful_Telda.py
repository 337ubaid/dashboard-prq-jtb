import streamlit as st
import pandas as pd
import textwrap
from typing import Any
from streamlit_echarts import st_echarts
from utils.helpers import setup_page
from utils.data_processing import (
    load_and_clean_monthly_data,
    TELDA_REGIONS,
)

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
    """Renders the dashboard page title and subtitle (G30)."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #1e3a8a; font-weight: 800; font-size: 32px; margin-bottom: 4px;">🏆 Impactful Telda</h1>
        </div>
        """,
        unsafe_allow_html=True,
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


def style_total_point_col(val: Any) -> str:
    """Applies a smooth color gradient to the Total Points column cell based on rank score (G30)."""
    if pd.isna(val) or val == "-":
        return ""
    try:
        v = float(val)
        if v >= 95.0:
            return "background-color: rgba(16, 185, 129, 0.25); color: #047857; font-weight: 800;"
        elif v >= 90.0:
            return "background-color: rgba(16, 185, 129, 0.15); color: #065f46; font-weight: 700;"
        elif v >= 80.0:
            return "background-color: rgba(245, 158, 11, 0.15); color: #b45309; font-weight: 700;"
        else:
            return "background-color: rgba(239, 68, 68, 0.15); color: #b91c1c; font-weight: 700;"
    except ValueError:
        return ""


def _prepare_score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares, reorders, and sorts the Score/POINT dataframe by TOTAL descending (G30)."""
    df = df.copy()
    metric_cols = [item["display"] for item in SCORECARD_METRICS]
    df["TOTAL"] = df[metric_cols].sum(axis=1)
    cols = ["TELDA", "TOTAL"] + metric_cols
    df_sorted = df[cols].sort_values(by="TOTAL", ascending=False)
    return df_sorted


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
    percentage_suffix: bool = False,
    is_score: bool = False
) -> None:
    """Formats and styles dataframes for standard display in the dashboard (G30)."""
    metric_cols = [item["display"] for item in SCORECARD_METRICS]

    if is_score:
        num_cols = [c for c in df.columns if c != "TELDA"]
        format_dict = {c: (lambda x: f"{x:,.2f}" if pd.notna(x) else "-") for c in num_cols}
        styled_df = df.style.format(format_dict).applymap(
            style_total_point_col, subset=["TOTAL"]
        )
    elif is_ach:
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

    st.dataframe(styled_df, width='stretch', hide_index=True)


def render_download_button(df: pd.DataFrame, filename: str, label: str) -> None:
    """Provides a unified standard CSV download button (G30)."""
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
    )


def _calculate_average_points_for_month(df_consolidated: pd.DataFrame, selected_month: str) -> float:
    """Calculate the average total points across all 8 Teldas for a specific month (G30)."""
    points = []
    for t in TELDA_REGIONS:
        df_subset = df_consolidated[(df_consolidated["TELDA"] == t) & (df_consolidated["MONTH"] == selected_month)]
        if not df_subset.empty:
            _, _, total_points = calculate_scorecard(df_subset)
            points.append(total_points)
    return float(pd.Series(points).mean()) if points else 0.0


def _render_executive_kpi_cards(
    selected_telda: str, 
    selected_month: str, 
    total_point: float, 
    point_diff: float
) -> None:
    """Render executive summary scorecard grid with high-fidelity glassmorphism layout (G30)."""
    if point_diff >= 0:
        diff_symbol = "▲"
        diff_color = "#10b981"
        diff_label = f"+{point_diff:.2f} di atas rata-rata"
    else:
        diff_symbol = "▼"
        diff_color = "#ef4444"
        diff_label = f"{point_diff:.2f} di bawah rata-rata"
        
    st.html(textwrap.dedent(f"""
        <style>
            .bento-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }}
            .bento-card {{
                padding: 20px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.6);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(226, 232, 240, 0.8);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .bento-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
            }}
            .bento-title {{
                font-size: 11px;
                color: #64748b;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
                margin-bottom: 12px;
            }}
            .bento-value {{
                font-size: 28px;
                font-weight: 800;
                color: #1e293b;
                line-height: 1.1;
                margin: 0;
            }}
            .bento-subtext {{
                font-size: 12px;
                color: #64748b;
                margin-top: 8px;
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            .badge {{
                display: inline-flex;
                align-items: center;
                padding: 2px 8px;
                border-radius: 9999px;
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
            }}
        </style>
              
        <div class="bento-container">
            <div class="bento-card" style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.03) 0%, rgba(59, 130, 246, 0.03) 100%);">
                <div>
                    <span class="bento-title">Wilayah & Periode</span>
                    <h2 class="bento-value" style="color: #1e3a8a; font-size: 24px;">{selected_telda}</h2>
                </div>
                <div class="bento-subtext">
                    <span class="badge" style="background: rgba(30, 58, 138, 0.1); color: #1e3a8a;">Bulan {selected_month}</span>
                </div>
            </div>
            
            <div class="bento-card" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.04) 0%, rgba(147, 51, 234, 0.04) 100%); border-color: rgba(59, 130, 246, 0.2);">
                <div>
                    <span class="bento-title" style="color: #4f46e5;">Total Point Scorecard</span>
                    <h2 class="bento-value" style="color: #4f46e5;">{total_point:.2f}</h2>
                </div>
                <div class="bento-subtext" style="color: #4f46e5; font-weight: 600;">
                    Nilai Kumulatif
                </div>
            </div>
            
            <div class="bento-card" style="border-left: 4px solid {diff_color};">
                <div>
                    <span class="bento-title">Performa vs Rata-rata</span>
                    <h2 class="bento-value" style="color: {diff_color}; display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 20px;">{diff_symbol}</span> {abs(point_diff):.2f} pts
                    </h2>
                </div>
                <div class="bento-subtext" style="color: #475569;">
                    {diff_label}
                </div>
            </div>
        </div>
    """))


def _render_monthly_trend_chart(
    months: list[str], 
    points: list[float], 
    averages: list[float], 
    selected_month: str
) -> None:
    """Render monthly points performance trend and regional averages using high-fidelity ECharts (G30)."""
    formatted_points = []
    for m, p in zip(months, points):
        if m == selected_month:
            formatted_points.append({
                "value": p,
                "symbolSize": 10,
                "itemStyle": {"color": "#1e3a8a", "borderColor": "#3b82f6", "borderWidth": 2},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c} pts",
                    "fontWeight": "bold",
                    "color": "#1e3a8a"
                }
            })
        else:
            formatted_points.append({
                "value": p,
                "symbolSize": 6,
                "itemStyle": {"color": "#3b82f6"}
            })

    options = {
        "title": {
            "text": "Monthly Performance Points Trend vs Regional Average",
            "textStyle": {"fontSize": 14, "fontWeight": "bold", "color": "#1e293b"},
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Total Points (TELDA)", "Rata-rata Regional"],
            "top": "bottom"
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "12%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": months,
            "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            "axisLabel": {"fontWeight": "bold", "color": "#475569"}
        },
        "yAxis": {
            "type": "value",
            "name": "Points",
            "min": 0,
            "max": 100,
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#e2e8f0"}}
        },
        "series": [
            {
                "name": "Total Points (TELDA)",
                "type": "line",
                "data": formatted_points,
                "smooth": True,
                "lineStyle": {"width": 3, "color": "#3b82f6"},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(59, 130, 246, 0.2)"},
                            {"offset": 1, "color": "rgba(59, 130, 246, 0.0)"}
                        ]
                    }
                }
            },
            {
                "name": "Rata-rata Regional",
                "type": "line",
                "data": averages,
                "smooth": True,
                "lineStyle": {"width": 3, "type": "dashed", "color": "#f59e0b"},
                "itemStyle": {"color": "#f59e0b"}
            }
        ]
    }
    
    st_echarts(options=options, height="380px")


def _render_actionable_insights(stars: list[dict], criticals: list[dict]) -> None:
    """Render Star Performers & Critical Focus Areas cards using high-fidelity styling (G30)."""
    st.html('<div style="margin-top: 15px;"></div>')
    st.markdown("### 💡 Actionable Insights & Recommendations")
    col_stars, col_crit = st.columns(2)
    
    with col_stars:
        stars_html = "".join([
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:13px; color:#065f46;">'
            f'<span style="font-weight:600;">{m["name"]}</span>'
            f'<span style="font-weight:700; background:rgba(209, 250, 229, 0.8); padding:2px 8px; border-radius:4px;">{m["ach"]:.1f}%</span>'
            f'</div>'
            for m in stars
        ])
        if not stars:
            stars_html = '<div style="font-size:13px; color:#64748b; font-style:italic;">Tidak ada metrik yang mencapai >= 100% target pada bulan ini.</div>'
            
        st.html(textwrap.dedent(f"""
            <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 16px; height: 100%;">
                <h4 style="margin-top:0; color:#047857; font-weight:700; display:flex; align-items:center; gap:6px;">
                    ⭐ Star Performers (≥ 100% Target)
                </h4>
                {stars_html}
            </div>
        """))
        
    with col_crit:
        criticals_html = "".join([
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:13px; color:#991b1b;">'
            f'<span style="font-weight:600;">{m["name"]}</span>'
            f'<span style="font-weight:700; background:rgba(254, 226, 230, 0.8); padding:2px 8px; border-radius:4px;">{m["ach"]:.1f}%</span>'
            f'</div>'
            for m in criticals
        ])
        if not criticals:
            criticals_html = '<div style="font-size:13px; color:#64748b; font-style:italic;">Hebat! Semua metrik berhasil mencapai >= 90% target pada bulan ini.</div>'
            
        st.html(textwrap.dedent(f"""
            <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 16px; height: 100%;">
                <h4 style="margin-top:0; color:#b91c1c; font-weight:700; display:flex; align-items:center; gap:6px;">
                    ⚠️ Critical Focus Areas (< 90% Target)
                </h4>
                {criticals_html}
            </div>
        """))


def main() -> None:
    """Main entrypoint of the Streamlit dashboard page (G30)."""
    setup_page("PRQ Dashboard | Impactful Telda")
    render_header()

    df_consolidated = load_and_clean_monthly_data()

    if df_consolidated.empty:
        st.warning("⚠️ Data bulanan kosong atau gagal memuat spreadsheet.")
        st.stop()

    # 1. Global Filters (at the top of the main screen)
    st.markdown("### 🔍 Filter Data Wilayah & Periode")
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
        # Default to the current month if available in the database (G30, G3)
        import datetime
        current_month_str = datetime.datetime.now().strftime("%Y%m")
        default_index = len(all_months) - 1
        if current_month_str in all_months:
            default_index = all_months.index(current_month_str)
            
        selected_month = st.selectbox(
            "Pilih Bulan:",
            options=all_months,
            index=default_index,
            key="analysis_month_filter",
        )

    if not selected_telda or not selected_month:
        st.warning("⚠️ Silakan pilih Wilayah Telda dan Bulan.")
        return

    # Filtered subset for single MTD row of chosen Telda and Month
    df_filtered_single = df_consolidated[
        (df_consolidated["TELDA"] == selected_telda)
        & (df_consolidated["MONTH"] == selected_month)
    ].copy()

    if df_filtered_single.empty:
        st.warning("⚠️ Tidak ada data untuk kombinasi ini.")
        return

    # Generate scorecard metrics for selected month
    df_scorecard, total_weight_sum, total_point_sum = calculate_scorecard(
        df_filtered_single
    )

    # Calculate performance difference vs regional average
    avg_point = _calculate_average_points_for_month(df_consolidated, selected_month)
    point_diff = total_point_sum - avg_point

    # 2. Summary KPI Cards
    st.markdown("### 🏆 Single Scorecard Summary")
    _render_executive_kpi_cards(selected_telda, selected_month, total_point_sum, point_diff)

    # 3. Main Tabs (QTD, MTD, and YTD)
    st.markdown("### 📈 Detail Pencapaian Indikator Kinerja")
    tab_qtd, tab_mtd, tab_ytd = st.tabs(
        [
            "📅 Quarter-to-Date (QTD)",
            "📊 Month-to-Date (MTD)",
            "📈 Year-to-Date (YTD)",
        ]
    )

    # --- Quarter-to-Date Tab ---
    with tab_qtd:
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

        st.dataframe(styled_qtd, width='stretch', hide_index=True)
        render_download_button(
            df_qtd,
            f"qtd_scorecard_{selected_telda.lower()}.csv",
            "📥 Unduh Tabel QTD Sebagai CSV",
        )

    # --- Month-to-Date Tab ---
    with tab_mtd:
        st.markdown(
            f"Kinerja seluruh Telda pada Bulan Terpilih **{selected_month}**."
        )

        df_mtd_t, df_mtd_r, df_mtd_a, df_mtd_s_raw = compile_regional_metrics(
            df_consolidated, [selected_month]
        )
        df_mtd_s = _prepare_score_dataframe(df_mtd_s_raw)

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
            render_styled_dataframe(df_mtd_s, is_score=True)
            render_download_button(
                df_mtd_s, f"mtd_score_{selected_month}.csv", "📥 Unduh MTD Score Sebagai CSV"
            )

    # --- Year-to-Date Tab ---
    with tab_ytd:
        st.markdown(
            f"Kinerja kumulatif seluruh Telda dari awal tahun s.d. Bulan Terpilih **{selected_month}**."
        )

        ytd_months = [m for m in all_months if m <= selected_month]
        df_ytd_t, df_ytd_r, df_ytd_a, df_ytd_s_raw = compile_regional_metrics(
            df_consolidated, ytd_months
        )
        df_ytd_s = _prepare_score_dataframe(df_ytd_s_raw)

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
            render_styled_dataframe(df_ytd_s, is_score=True)
            render_download_button(
                df_ytd_s, f"ytd_score_{selected_month}.csv", "📥 Unduh YTD Score Sebagai CSV"
            )

    # 4. Performance Storytelling Section
    st.markdown("---")
    st.markdown("### 📈 Analisis Performa & Visualisasi Storytelling")
    
    # Calculate monthly points trend for the chosen Telda & Regional Average
    trend_months = []
    trend_points = []
    trend_averages = []
    for m in all_months:
        df_m = df_consolidated[(df_consolidated["TELDA"] == selected_telda) & (df_consolidated["MONTH"] == m)]
        if not df_m.empty:
            _, _, total_points = calculate_scorecard(df_m)
            trend_months.append(m)
            trend_points.append(round(total_points, 2))
            
            avg_pts = _calculate_average_points_for_month(df_consolidated, m)
            trend_averages.append(round(avg_pts, 2))
            
    col_chart, col_empty = st.columns([3, 1])
    with col_chart:
        _render_monthly_trend_chart(trend_months, trend_points, trend_averages, selected_month)
        
    # Extract achievements from MTD scorecard to render Actionable Insights
    all_metrics_performances = []
    for idx, row in df_scorecard.iterrows():
        all_metrics_performances.append({
            "name": str(row["Indikator"]),
            "ach": float(row["Achievement (ACH)"])
        })
        
    stars = [m for m in all_metrics_performances if m["ach"] >= ACH_EXCELLENT_THRESHOLD]
    criticals = [m for m in all_metrics_performances if m["ach"] < ACH_GOOD_THRESHOLD]
    
    _render_actionable_insights(stars, criticals)

    # 5. Detailed Monthly Audit Trail
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
    st.dataframe(df_filtered_single.style.format(detail_format), width='stretch')


if __name__ == "__main__":
    main()
