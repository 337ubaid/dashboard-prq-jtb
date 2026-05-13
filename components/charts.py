import streamlit as st
from streamlit_echarts import st_echarts

PRIMARY_COLOR = "#E60000"

def render_bar_chart(categories: list[str], values: list[float | int], title: str = "") -> None:
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
                    "color": PRIMARY_COLOR
                }
            }
        ]
    }
    st_echarts(options=options, height="400px")
