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
from utils.data_processing import load_and_clean_data, build_scorecard_table, clean_numeric_val
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


def _aggregate_scorecard_data(
    df_filtered: pd.DataFrame, 
    selected_teldas: list[str], 
    selected_quarters: list[str]
) -> pd.DataFrame:
    """
    Aggregate multiple scorecard rows into a single-row DataFrame (G30).
    Points and percentage metrics are averaged, while counts and revenue are summed.
    Matches clean code principles (G30 - functions do one thing, G3 - boundaries).
    """
    if df_filtered.empty:
        return pd.DataFrame()
        
    df_filtered = df_filtered.copy()
    agg_row = {}
    
    # 1. Handle TELDA and QUARTER names
    agg_row["TELDA"] = ", ".join(selected_teldas) if len(selected_teldas) > 1 else selected_teldas[0]
    agg_row["QUARTER"] = ", ".join(selected_quarters) if len(selected_quarters) > 1 else selected_quarters[0]
    
    # 2. Handle RANK: "-" if more than 1 Quarter or more than 1 Telda is selected
    if len(selected_quarters) > 1 or len(selected_teldas) > 1:
        agg_row["RANK"] = "-"
    else:
        agg_row["RANK"] = str(df_filtered["RANK"].values[0]) if "RANK" in df_filtered.columns else "-"
        
    # Clean numeric values for all other columns before aggregating
    cleaned_df = pd.DataFrame()
    for col in df_filtered.columns:
        if col in ["TELDA", "QUARTER", "RANK"]:
            continue
        cleaned_df[col] = df_filtered[col].apply(clean_numeric_val)
        
    # 3. Aggregate columns
    for col in cleaned_df.columns:
        if col.endswith("TARGET") or col.endswith("REALIASASI") or col.endswith("REALISASI"):
            is_percentage = any(pct_indicator in col.upper() for pct_indicator in ["LTS", "VISIT", "C3MR"])
            if is_percentage:
                agg_row[col] = cleaned_df[col].mean()
            else:
                agg_row[col] = cleaned_df[col].sum()
        elif col.endswith("POINT") or col == "TOTAL POINT":
            agg_row[col] = cleaned_df[col].mean()
            
    # 4. Recalculate ACH columns based on aggregated Target and Realisasi for mathematical accuracy
    for col in df_filtered.columns:
        if any(col.endswith(suffix) for suffix in ["- ACH", " - ACH", " -ACH", "-ACH"]):
            suffix_len = 0
            for suffix in ["- ACH", " - ACH", " -ACH", "-ACH"]:
                if col.endswith(suffix):
                    suffix_len = len(suffix)
                    break
            prefix = col[:-suffix_len].strip()
            
            target_col = next((c for c in agg_row.keys() if c.strip().upper().startswith(prefix.upper()) and c.strip().upper().endswith("TARGET")), None)
            real_col = next((c for c in agg_row.keys() if c.strip().upper().startswith(prefix.upper()) and (c.strip().upper().endswith("REALIASASI") or c.strip().upper().endswith("REALISASI"))), None)
            
            if target_col and real_col:
                target_val = agg_row[target_col]
                real_val = agg_row[real_col]
                agg_row[col] = (real_val / target_val * 100) if target_val > 0 else 0.0
            else:
                agg_row[col] = cleaned_df[col].mean()
                
    return pd.DataFrame([agg_row])


def main() -> None:
    """Main entry point to build and render the Impactful Telda dashboard page."""
    df = load_and_clean_data()
    col_filter, col_content = st.columns([1, 4])
    
    with col_filter:
        with st.container(height=FILTER_CONTAINER_HEIGHT):
            st.subheader("Filter Data")      
            
            quarter_options = ["Q1", "Q2", "Q3", "Q4"]
            selected_quarters = st.multiselect(
                "QUARTER", 
                options=quarter_options, 
                default=[quarter_options[0]],
                help="Pilih satu atau lebih kuartal."
            )

            telda_options = ["BATU", "BLITAR", "BOJONEGORO", "KEDIRI", "MADIUN", "MALANG", "NGANJUK", "PONOROGO"]
            selected_teldas = st.multiselect(
                "TELDA", 
                options=telda_options, 
                default=[telda_options[0]],
                help="Pilih satu atau lebih TELDA."
            )
                
    if not selected_quarters or not selected_teldas:
        with col_content:
            st.warning("⚠️ Silakan pilih minimal satu QUARTER dan satu TELDA pada filter di sebelah kiri.")
        return
        
    df_filtered = df.copy()
    if not df_filtered.empty:
        df_filtered = df_filtered[
            df_filtered["TELDA"].str.upper().isin([t.strip().upper() for t in selected_teldas]) &
            df_filtered["QUARTER"].str.upper().isin([q.strip().upper() for q in selected_quarters])
        ]
        
    with col_content:      
        if df_filtered.empty:
            st.warning("⚠️ Tidak ada data yang cocok dengan kombinasi filter terpilih.")
            return
            
        df_aggregated = _aggregate_scorecard_data(df_filtered, selected_teldas, selected_quarters)
        
        total_point = float(df_aggregated["TOTAL POINT"].values[0]) if "TOTAL POINT" in df_aggregated.columns else 0.0
        rank_val = str(df_aggregated["RANK"].values[0]) if "RANK" in df_aggregated.columns else "-"
        
        df_quarters = df[df["QUARTER"].str.upper().isin([q.strip().upper() for q in selected_quarters])]
        avg_point = 0.0
        if not df_quarters.empty:
            df_quarters_points = pd.to_numeric(df_quarters["TOTAL POINT"], errors='coerce').fillna(0)
            avg_point = df_quarters_points.mean()
        point_diff = total_point - avg_point
        
        selected_telda_label = ", ".join(selected_teldas) if len(selected_teldas) <= 3 else f"{len(selected_teldas)} TELDA"
        selected_quarter_label = ", ".join(selected_quarters)
        
        # Render top executives KPI cards (G30)
        _render_executive_kpi_cards(selected_telda_label, selected_quarter_label, rank_val, total_point, point_diff)
        
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
        
        # Build scorecard tables once using aggregated data (G5 DRY - single source of truth)
        rev_scorecard = build_scorecard_table(df_aggregated, revenue_mapping)
        sales_scorecard = build_scorecard_table(df_aggregated, sales_mapping)
        ops_scorecard = build_scorecard_table(df_aggregated, operational_mapping)
        
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
                    width="stretch"
                )
                
        with tab_sales:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("2. Sales & Digital Products")
                st.dataframe(
                    style_scorecard(sales_scorecard.style, format_count),
                    width="stretch"
                )
                
        with tab_ops:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("3. Operational Metrics")
                st.dataframe(
                    style_scorecard(ops_scorecard.style, lambda x: f"{x:.2f}%"),
                    width="stretch"
                )
                
        with tab_analytics:
            with st.container(height=CONTENT_CONTAINER_HEIGHT - 60):
                st.subheader("Analisis Performa & Visualisasi Storytelling")
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    render_leaderboard_chart(df, selected_quarters, selected_teldas)
                    
                with col_chart2:
                    render_trend_chart(df, selected_teldas)
                
                # Render stars and criticals insight blocks (G30)
                _render_actionable_insights(stars, criticals)


if __name__ == "__main__":
    main()

