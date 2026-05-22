import streamlit as st

def render_kpi_card(title: str, value: str, delta: str | None = None) -> None:
    """
    Render a standard Streamlit metric card.
    """
    st.metric(label=title, value=value, delta=delta)
