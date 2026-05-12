import streamlit as st
from streamlit_echarts import st_echarts

def render_bar_chart(categories: list, values: list, title: str = ""):
    """
    Render a simple bar chart using ECharts.
    """
    options = {
        "title": {
            "text": title
        },
        "tooltip": {
            "trigger": "axis"
        },
        "xAxis": {
            "type": "category",
            "data": categories
        },
        "yAxis": {
            "type": "value"
        },
        "series": [
            {
                "data": values,
                "type": "bar",
                "itemStyle": {
                    "color": "#E60000" # Warna custom sesuai tema
                }
            }
        ]
    }
    st_echarts(options=options, height="400px")
