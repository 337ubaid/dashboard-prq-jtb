import streamlit as st
import pandas as pd
from typing import Callable, Any
from pandas.io.formats.style import Styler

# Styling and Highlight CSS Constants (G25)
CSS_TOTAL_HIGHLIGHT = "background-color: #d2e9f9; font-weight: bold; color: #000000"
CSS_ACH_EXCELLENT = "background-color: #d1fae5; font-weight: bold; color: #065f46"  # Achievement >= 100% (Green)
CSS_ACH_GOOD = "background-color: #fef3c7; font-weight: bold; color: #92400e"       # Achievement >= 90% (Orange/Amber)
CSS_ACH_POOR = "background-color: #fee2e2; font-weight: bold; color: #991b1b"       # Achievement < 90% (Red)
CSS_ACH_DEFAULT = "background-color: #f3f4f6; font-weight: bold; color: #1f2937"    # Fallback/Error state


def format_short_number(value: float) -> str:
    """Format a number into Indonesian short string (Tr, M, Jt, Rb) (G30)."""
    if value >= 1e12:
        return f"{value / 1e12:.2f} Tr".replace('.', ',')
    elif value >= 1e9:
        return f"{value / 1e9:.2f} M".replace('.', ',')
    elif value >= 1e6:
        return f"{value / 1e6:.2f} Jt".replace('.', ',')
    elif value >= 1e3:
        return f"{value / 1e3:.2f} Rb".replace('.', ',')
    else:
        return f"{value:.0f}"


def setup_page(title: str, icon: str = "📊") -> None:
    """Setup default page configuration and styling for all pages."""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
            .block-container {
                padding-top: 2rem !important;
                padding-bottom: 0rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
        </style>
    """, unsafe_allow_html=True)


def highlight_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Highlight 'Total' row/column and 'Achievement' row dynamically (G30)."""
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    
    if 'Total' in styles.index:
        styles.loc['Total', :] = CSS_TOTAL_HIGHLIGHT
        
    if 'Achievement' in styles.index:
        for col in df.columns:
            val = df.loc['Achievement', col]
            try:
                val_float = float(val)
                if val_float >= 100.0:
                    styles.loc['Achievement', col] = CSS_ACH_EXCELLENT
                elif val_float >= 90.0:
                    styles.loc['Achievement', col] = CSS_ACH_GOOD
                else:
                    styles.loc['Achievement', col] = CSS_ACH_POOR
            except (ValueError, TypeError):
                styles.loc['Achievement', col] = CSS_ACH_DEFAULT
        
    if 'Total' in styles.columns:
        styles.loc[:, 'Total'] = CSS_TOTAL_HIGHLIGHT
        
    return styles


# Target Threshold Constants (G25, P2)
TARGET_EXCELLENT = 100.0
TARGET_GOOD = 90.0


def format_revenue(val: Any) -> str:
    """Format numerical value to Indonesian Rupiah standard format."""
    if val is None or pd.isna(val):
        return "-"
    return f"Rp {float(val):,.0f}".replace(",", ".")


def format_percentage(val: Any) -> str:
    """Format numerical value to standard percentage format."""
    if val is None or pd.isna(val):
        return "-"
    return f"{float(val):.2f}%"


def format_count(val: Any) -> str:
    """Format numerical counts into Indonesian formatted string."""
    if val is None or pd.isna(val):
        return "-"
    return f"Rp {float(val):,.0f}".replace(",", ".") if float(val) > 1000 else f"{float(val):,.0f}".replace(",", ".")


def style_scorecard(styler: Styler, value_formatter: Callable[[Any], str]) -> Styler:
    """Consolidated scorecard styling logic for all scorecards (G5, G30)."""
    styler = styler.set_properties(**{
        'font-family': 'Inter, sans-serif',
        'text-align': 'right',
        'padding': '10px 14px'
    })
    styler = styler.format(subset=['TARGET', 'REALISASI'], formatter=value_formatter)
    styler = styler.format(subset=['ACHIEVEMENT'], formatter=lambda x: f"{x:.2f}%")
    styler = styler.format(subset=['POINT'], formatter=lambda x: f"{x:.2f}")
    
    def color_achievement(val: Any) -> str:
        try:
            val_float = float(val)
            if val_float >= TARGET_EXCELLENT:
                return 'background-color: rgba(16, 185, 129, 0.15); color: #047857; font-weight: bold; border-radius: 4px;'
            elif val_float >= TARGET_GOOD:
                return 'background-color: rgba(245, 158, 11, 0.15); color: #b45309; font-weight: bold; border-radius: 4px;'
            else:
                return 'background-color: rgba(239, 68, 68, 0.15); color: #b91c1c; font-weight: bold; border-radius: 4px;'
        except Exception:
            return ''
            
    def color_point(val: Any) -> str:
        return 'font-weight: 700; color: #1e3a8a; background-color: rgba(30, 58, 138, 0.05);'
        
    styler = styler.map(color_achievement, subset=['ACHIEVEMENT'])
    styler = styler.map(color_point, subset=['POINT'])
    return styler



