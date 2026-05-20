import streamlit as st
import pandas as pd

def format_currency(value: float) -> str:
    """
    Format a number as Indonesian Rupiah.
    """
    return f"Rp {value:,.0f}".replace(",", ".")

def format_short_number(value: float) -> str:
    """
    Format a number into Indonesian short string (Tr, M, Jt, Rb).
    """
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

def setup_page(title: str, icon: str = "📊"):
    """
    Setup default page configuration and styling for all pages.
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 0rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

def highlight_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mengembalikan dataframe berisi konfigurasi CSS untuk melakukan highlight 
    pada baris 'Total' dan kolom 'Total'.
    """
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    
    if 'Total' in styles.index:
        styles.loc['Total', :] = 'background-color: #fef3c7; font-weight: bold; color: #000000'
        
    if 'Total' in styles.columns:
        styles.loc[:, 'Total'] = 'background-color: #fef3c7; font-weight: bold; color: #000000'
        
    return styles

