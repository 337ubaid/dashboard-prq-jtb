import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_echarts import st_echarts
from utils.data_processing import get_filter_options, get_pivoted_data_from_bq, get_layanan_pivoted_data_from_bq, get_top_bottom_pelanggan_from_bq
from utils.helpers import setup_page, highlight_totals, format_short_number
from data.processing import TARGET_REVENUE_BY_PERIOD

setup_page(title="PRQ Dashboard | Detail")

st.title("CBASE SME")

# Page Layout and Styling Constants (G25)
FILTER_CONTAINER_HEIGHT = 750
CONTENT_CONTAINER_HEIGHT = 690

# Achievement Threshold Constants (G25, P2)
ACHIEVEMENT_EXCELLENT = 100.0
ACHIEVEMENT_GOOD = 90.0

COLOR_EMERALD_GREEN = "#10b981"
COLOR_AMBER_ORANGE = "#f59e0b"
COLOR_ROSE_RED = "#ef4444"
COLOR_ACTUAL_REVENUE = "#1f77b4"
COLOR_TARGET_REVENUE = "#38bdf8"


def _render_sidebar_filters(filter_opts: dict[str, list]) -> dict[str, any]:
    """Render sidebar filters and return the selected values (G30)."""
    with st.container(height=FILTER_CONTAINER_HEIGHT):
        st.subheader("Filter Data")
        
        filters = {}
        current_year = datetime.now().year
        default_year = [current_year] if current_year in filter_opts["years"] else []
        
        filters["years"] = st.multiselect("Tahun", options=filter_opts["years"], default=default_year)
        filters["nipnas_search"] = st.text_input("Cari NO NIPNAS", value="")
        filters["flags"] = st.multiselect("FLAG REVENUE", options=filter_opts["flags"], default=[])
        filters["subsegmen"] = st.multiselect("SUBSEGMEN HO", options=filter_opts["subsegmen"], default=[])
        filters["bam"] = st.multiselect("NAMA AM", options=filter_opts["bam"], default=[])
        filters["telda"] = st.multiselect("TELDA", options=filter_opts["telda"], default=[])
        filters["sto"] = st.multiselect("STO", options=filter_opts["sto"], default=[])
        
        sharepoint_url = st.secrets["sharepoint"]["cek_nama_pelanggan"]
        st.markdown(f"🔗 [Cek Nama Pelanggan]({sharepoint_url})")
        
        return filters


def main() -> None:
    """Main function to run the CBASE SME dashboard page."""
    try:
        filter_opts = get_filter_options()
        col_filter, col_content = st.columns([1, 4])
        
        with col_filter:
            filters = _render_sidebar_filters(filter_opts)
                
        with col_content:
            tab_chart, tab_layanan, tab_pelanggan = st.tabs(["Overview", "Layanan", "Rank Pelanggan"])
            
            with tab_chart:            
                render_overview_tab(filters)
                
            with tab_layanan:
                render_layanan_tab(filters)
                
            with tab_pelanggan:
                render_pelanggan_tab(filters)
    except Exception as e:
        st.error(f"Gagal mengambil data dari BigQuery: {e}")


def _calculate_summary_metrics(pivot_df: pd.DataFrame, x_axis_data: list[str]) -> tuple[float, float, float]:
    """Calculate actual revenue, target revenue, and overall achievement rate (G30)."""
    total_actual = float(pivot_df.loc['Total'].sum())
    total_target = float(sum(
        TARGET_REVENUE_BY_PERIOD.get(p, 0)
        for p in x_axis_data
        if TARGET_REVENUE_BY_PERIOD.get(p) is not None
    ))
    overall_achievement = (total_actual / total_target * 100) if total_target > 0 else 0.0
    return total_actual, total_target, overall_achievement


def _get_achievement_color(overall_achievement: float) -> str:
    """Determine color dynamically based on achievement rate (G30)."""
    if overall_achievement >= ACHIEVEMENT_EXCELLENT:
        return COLOR_EMERALD_GREEN
    if overall_achievement >= ACHIEVEMENT_GOOD:
        return COLOR_AMBER_ORANGE
    return COLOR_ROSE_RED


def _render_summary_kpi_cards(total_actual: float, total_target: float, overall_achievement: float) -> None:
    """Render modern glassmorphic summary KPI blocks (G30)."""
    ach_color = _get_achievement_color(overall_achievement)
    st.markdown(f"""
        <style>
            .kpi-container {{
                display: flex;
                gap: 16px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .kpi-card {{
                flex: 1;
                min-width: 200px;
                padding: 16px 20px;
                border-radius: 12px;
                background: rgba(128, 128, 128, 0.06);
                border: 1px solid rgba(128, 128, 128, 0.12);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            .kpi-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07);
                background: rgba(128, 128, 128, 0.09);
            }}
            .kpi-title {{
                font-size: 11px;
                color: #718096;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-bottom: 6px;
                display: block;
            }}
            .kpi-value {{
                font-size: 22px;
                font-weight: 700;
                margin: 0;
                line-height: 1.2;
            }}
            .progress-bar-bg {{
                width: 100%;
                height: 6px;
                background: rgba(128, 128, 128, 0.15);
                border-radius: 3px;
                margin-top: 10px;
                overflow: hidden;
            }}
            .progress-bar-fill {{
                height: 100%;
                border-radius: 3px;
                box-shadow: 0 0 6px rgba(0,0,0,0.1);
                transition: width 1s ease-in-out;
            }}
        </style>
        <div class="kpi-container">
            <div class="kpi-card">
                <span class="kpi-title">Actual Revenue (YTD)</span>
                <h2 class="kpi-value" style="color: {COLOR_ACTUAL_REVENUE};">Rp {format_short_number(total_actual)}</h2>
            </div>
            <div class="kpi-card">
                <span class="kpi-title">Target Revenue (YTD)</span>
                <h2 class="kpi-value" style="color: {COLOR_TARGET_REVENUE};">Rp {format_short_number(total_target)}</h2>
            </div>
            <div class="kpi-card">
                <span class="kpi-title">Overall Achievement</span>
                <h2 class="kpi-value" style="color: {ach_color};">{overall_achievement:.1f}%</h2>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {min(overall_achievement, 100.0):.1f}%; background: {ach_color}; box-shadow: 0 0 8px {ach_color};"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def _render_revenue_chart(x_axis_data: list[str], series_data: list[dict]) -> None:
    """Render the total revenue trend line chart using ECharts (G30)."""
    target_values = [TARGET_REVENUE_BY_PERIOD.get(p) for p in x_axis_data]
    
    chart_series = series_data.copy()
    chart_series.append({
        "name": "Target Revenue",
        "type": "line",
        "data": target_values,
        "smooth": True,
        "itemStyle": {"color": COLOR_TARGET_REVENUE},
        "lineStyle": {"type": "dashed"}
    })

    options = {
        "title": {"text": "Trend Total Revenue"},
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Total Revenue", "Target Revenue"],
            "top": "bottom"
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
        "toolbox": {
            "feature": {
                "saveAsImage": {}
            }
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": x_axis_data
        },
        "yAxis": {
            "type": "value"
        },
        "series": chart_series
    }

    st.subheader("Trend Total Revenue")
    st_echarts(options=options, height="350px")


def _add_achievement_row(pivot_df: pd.DataFrame, total_actual: float, total_target: float) -> pd.DataFrame:
    """Calculate and append target achievement row values to pivot table (G30)."""
    df_copy = pivot_df.copy()
    achievement_row = {}
    
    for col in df_copy.columns:
        if col in TARGET_REVENUE_BY_PERIOD:
            target_val = TARGET_REVENUE_BY_PERIOD.get(col)
            if target_val and target_val > 0:
                actual_val = df_copy.loc['Total', col]
                achievement_row[col] = (actual_val / target_val) * 100
            else:
                achievement_row[col] = 0.0
        elif col == 'Total':
            achievement_row[col] = (total_actual / total_target * 100) if total_target > 0 else 0.0
        else:
            achievement_row[col] = 0.0
            
    df_copy.loc['Achievement'] = pd.Series(achievement_row)
    return df_copy


def _render_revenue_dataframe(pivot_df: pd.DataFrame) -> None:
    """Apply styling formatters and render the custom detailed table in Streamlit (G30)."""
    st.subheader("Tabel Revenue")
    
    non_ach_rows = [idx for idx in pivot_df.index if idx != 'Achievement']
    styler = pivot_df.style.apply(highlight_totals, axis=None)
    styler = styler.format(subset=(non_ach_rows, pivot_df.columns), thousands=".", precision=0)
    styler = styler.format(subset=(['Achievement'], pivot_df.columns), formatter="{:.1f}%")

    st.dataframe(styler, width="stretch")


def render_overview_tab(filters: dict[str, any]) -> None:
    """Orchestrate layout loading and visualization render for the Overview Tab (G30, G34)."""
    with st.container(height=CONTENT_CONTAINER_HEIGHT):
        result = get_pivoted_data_from_bq(filters)
        
        if result[0] is not None:
            pivot_df, x_axis_data, series_data = result
            
            total_actual, total_target, overall_achievement = _calculate_summary_metrics(pivot_df, x_axis_data)
            
            _render_summary_kpi_cards(total_actual, total_target, overall_achievement)
            _render_revenue_chart(x_axis_data, series_data)
            
            pivot_df_with_ach = _add_achievement_row(pivot_df, total_actual, total_target)
            _render_revenue_dataframe(pivot_df_with_ach)
        else:
            st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")


def render_layanan_tab(filters: dict[str, any]) -> None:
    """Orchestrate layout loading and rendering for the Layanan Tab (G30)."""
    with st.container(height=CONTENT_CONTAINER_HEIGHT):
        st.subheader("Tabel Revenue per Layanan")
        
        pivot_df = get_layanan_pivoted_data_from_bq(filters)
        
        if pivot_df is not None:
            st.dataframe(
                pivot_df.style.apply(highlight_totals, axis=None).format(thousands=".", precision=0), 
                width="stretch"
            )
        else:
            st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")


def render_pelanggan_tab(filters: dict[str, any]) -> None:
    """Orchestrate layout loading and rendering for the Top/Bottom Customers Tab (G30)."""
    with st.container(height=CONTENT_CONTAINER_HEIGHT):
        st.subheader("Rank 10 Pelanggan")
        
        top_df, bottom_df = get_top_bottom_pelanggan_from_bq(filters, n=10)
        
        if top_df is not None and bottom_df is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top 10 Pelanggan**")
                st.dataframe(
                    top_df.style.format(thousands=".", precision=0), 
                    width="stretch"
                )
                
            with col2:
                st.markdown("**Bottom 10 Pelanggan**")
                st.dataframe(
                    bottom_df.style.format(thousands=".", precision=0), 
                    width="stretch"
                )
        else:
            st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")


if __name__ == "__main__":
    main()

