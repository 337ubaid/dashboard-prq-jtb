import streamlit as st
import pandas as pd
import textwrap
from utils.helpers import (
    setup_page,
    style_scorecard,
    format_revenue,
    format_count,
    TARGET_EXCELLENT,
    TARGET_GOOD
)
from utils.data_processing import load_and_clean_data, build_scorecard_table
from components.charts import render_leaderboard_chart, render_trend_chart

# Setup standard page configuration for Impactful Telda
setup_page("PRQ Dashboard | Impactful Telda")

st.title("Impactful Telda")

# Page Layout and Styling Constants (G25)
FILTER_CONTAINER_HEIGHT = 750
CONTENT_CONTAINER_HEIGHT = 690

COLOR_EMERALD_GREEN = "#10b981"
COLOR_AMBER_ORANGE = "#f59e0b"
COLOR_ROSE_RED = "#ef4444"
COLOR_PRIMARY_BLUE = "#1e3a8a"


def _get_rank_styling(rank_val: str) -> tuple[str, str, str, str]:
    """Determine ranking badge, border, and background styling colors based on value (G30)."""
    try:
        rank_num = int(float(rank_val))
        if rank_num <= 2:
            return ("rgba(16, 185, 129, 0.08)", "rgba(16, 185, 129, 0.3)", "#047857", "🏆 Top Performer")
        elif rank_num <= 5:
            return ("rgba(245, 158, 11, 0.08)", "rgba(245, 158, 11, 0.3)", "#b45309", "👍 Average Performer")
        else:
            return ("rgba(239, 68, 68, 0.08)", "rgba(239, 68, 68, 0.3)", "#b91c1c", "⚠️ Needs Improvement")
    except Exception:
        return ("rgba(128, 128, 128, 0.06)", "rgba(128, 128, 128, 0.12)", "#475569", "-")


def _render_executive_kpi_cards(
    selected_telda: str, 
    selected_quarter: str, 
    rank_val: str, 
    total_point: float, 
    point_diff: float
) -> None:
    """Render executive summary scorecard grid with high-fidelity glassmorphism layout (G30)."""
    rank_bg, rank_border, rank_color, rank_badge = _get_rank_styling(rank_val)
    
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
                    <span class="badge" style="background: rgba(30, 58, 138, 0.1); color: #1e3a8a;">Kuartal {selected_quarter}</span>
                </div>
            </div>
            
            <div class="bento-card" style="background: {rank_bg}; border-color: {rank_border};">
                <div>
                    <span class="bento-title" style="color: {rank_color};">Peringkat (Rank)</span>
                    <h2 class="bento-value" style="color: {rank_color};">Rank {rank_val}</h2>
                </div>
                <div class="bento-subtext" style="color: {rank_color}; font-weight: 600;">
                    {rank_badge}
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


def _render_actionable_insights(stars: list[dict], criticals: list[dict]) -> None:
    """Render beautiful Star Performers & Critical Focus Areas cards using high-fidelity styling (G30)."""
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
            stars_html = '<div style="font-size:13px; color:#64748b; font-style:italic;">Tidak ada metrik yang mencapai >= 100% target pada kuartal ini.</div>'
            
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
            criticals_html = '<div style="font-size:13px; color:#64748b; font-style:italic;">Hebat! Semua metrik berhasil mencapai >= 90% target pada kuartal ini.</div>'
            
        st.html(textwrap.dedent(f"""
            <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 16px; height: 100%;">
                <h4 style="margin-top:0; color:#b91c1c; font-weight:700; display:flex; align-items:center; gap:6px;">
                    ⚠️ Critical Focus Areas (< 90% Target)
                </h4>
                {criticals_html}
            </div>
        """))


def main() -> None:
    """Main entry point to build and render the Impactful Telda dashboard page."""
    df = load_and_clean_data()
    col_filter, col_content = st.columns([1, 4])
    
    with col_filter:
        with st.container(height=FILTER_CONTAINER_HEIGHT):
            st.subheader("Filter Data")      
            
            quarter_options = ["Q1", "Q2", "Q3", "Q4"]
            selected_quarter = st.segmented_control(
                "QUARTER", 
                options=quarter_options, 
                help="Pilih salah satu kuartal.",
                default=quarter_options[0],
                width="stretch",
            )

            telda_options = ["BATU", "BLITAR", "BOJONEGORO", "KEDIRI", "MADIUN", "MALANG", "NGANJUK", "PONOROGO"]
            selected_telda = st.selectbox(
                "TELDA", 
                options=telda_options, 
                help="Pilih salah satu TELDA."
            )
            
            # with st.expander("🔍 Status Koneksi & Seluruh Data", expanded=False):
            #     if not df.empty:
            #         st.success(f"✅ Berhasil memuat `{len(df)}` baris data!")
            #         st.markdown("**Semua Record / Data Mentah:**")
            #         st.dataframe(df, use_container_width=True)
            #     else:
            #         st.warning("⚠️ Belum ada data yang termuat. Silakan masukkan link spreadsheet valid di secrets.toml.")
                
    df_filtered = df.copy()
    if not df_filtered.empty:
        if selected_telda:
            df_filtered = df_filtered[df_filtered["TELDA"] == selected_telda.strip().upper()]
        if selected_quarter:
            df_filtered = df_filtered[df_filtered["QUARTER"] == selected_quarter.strip().upper()]
        
    with col_content:      
        if df_filtered.empty:
            st.warning("⚠️ Tidak ada data yang cocok dengan kombinasi filter terpilih.")
            return
            
        total_point = float(df_filtered["TOTAL POINT"].values[0]) if "TOTAL POINT" in df_filtered.columns else 0.0
        rank_val = str(df_filtered["RANK"].values[0]) if "RANK" in df_filtered.columns else "-"
        
        df_quarter = df[df["QUARTER"] == selected_quarter.strip().upper()]
        avg_point = 0.0
        if not df_quarter.empty:
            df_quarter_points = pd.to_numeric(df_quarter["TOTAL POINT"], errors='coerce').fillna(0)
            avg_point = df_quarter_points.mean()
        point_diff = total_point - avg_point
        
        # Render top executives KPI cards (G30)
        _render_executive_kpi_cards(selected_telda, selected_quarter, rank_val, total_point, point_diff)
        
        revenue_mapping = {
            "POTS SME": "REV SME - POTS",
            "NONPOTS SME": "REV SME - NON POTS",
            "GOV": "REV GOV",
            "PS": "REV PS",
            "SOE": "REV SOE"
        }
        
        sales_mapping = {
            "HSI": "HSI ALL SEGMENT",
            "BW": "BW",
            "OCA": "OCA",
            "NETMONK": "NETMONK",
            "ANTARES EAZY": "EAZY",
            "PIJAR": "PIJAR SEKOLAH"
        }
        
        operational_mapping = {
            "LTS": "LTS",
            "VISIT": "VISIT"
        }
        
        # Build scorecard tables once (G5 DRY - single source of truth)
        rev_scorecard = build_scorecard_table(df_filtered, revenue_mapping)
        sales_scorecard = build_scorecard_table(df_filtered, sales_mapping)
        ops_scorecard = build_scorecard_table(df_filtered, operational_mapping)
        
        # Extract achievements directly from the generated scorecards (G5 DRY)
        all_metrics_performances = []
        for scorecard_df in [rev_scorecard, sales_scorecard, ops_scorecard]:
            if not scorecard_df.empty:
                for idx, row in scorecard_df.iterrows():
                    all_metrics_performances.append({
                        "name": str(idx),
                        "ach": float(row["ACHIEVEMENT"])
                    })
                    
        stars = [m for m in all_metrics_performances if m["ach"] >= TARGET_EXCELLENT]
        criticals = [m for m in all_metrics_performances if m["ach"] < TARGET_GOOD]
        
        tab_revenue, tab_sales, tab_ops, tab_analytics = st.tabs([
            "📊 Revenue Scorecard", 
            "🛍️ Sales & Products", 
            "⚙️ Operational Metrics",
            "📈 Storytelling & Leaderboard"
        ])
        
        with tab_revenue:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("1. Revenue Segmen")
                st.dataframe(
                    style_scorecard(rev_scorecard.style, format_revenue),
                    use_container_width=True
                )
                
        with tab_sales:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("2. Sales & Digital Products")
                st.dataframe(
                    style_scorecard(sales_scorecard.style, format_count),
                    use_container_width=True
                )
                
        with tab_ops:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("3. Operational Metrics")
                st.dataframe(
                    style_scorecard(ops_scorecard.style, lambda x: f"{x:.2f}%"),
                    use_container_width=True
                )
                
        with tab_analytics:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("Analisis Performa & Visualisasi Storytelling")
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    render_leaderboard_chart(df, selected_quarter, selected_telda)
                    
                with col_chart2:
                    render_trend_chart(df, selected_telda)
                
                # Render stars and criticals insight blocks (G30)
                _render_actionable_insights(stars, criticals)


if __name__ == "__main__":
    main()

