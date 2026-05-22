import streamlit as st
import pandas as pd
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


# Sorting and ECharts configuration constants (G25)
QUARTER_SORT_MAP = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}


def render_leaderboard_chart(df: pd.DataFrame, selected_quarter: str, selected_telda: str) -> None:
    """Render standard leaderboard bar chart using ECharts (G30)."""
    df_q = df[df["QUARTER"] == selected_quarter].copy()
    if df_q.empty:
        return
        
    df_q["TOTAL POINT"] = pd.to_numeric(df_q["TOTAL POINT"], errors='coerce').fillna(0)
    df_q = df_q.sort_values(by="TOTAL POINT", ascending=True)
    
    teldas = df_q["TELDA"].tolist()
    points = df_q["TOTAL POINT"].tolist()
    
    series_data = []
    for t, p in zip(teldas, points):
        if t.upper() == selected_telda.upper():
            series_data.append({
                "value": p,
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 1, "y2": 0,
                        "colorStops": [
                            {"offset": 0, "color": "#3b82f6"},
                            {"offset": 1, "color": "#1d4ed8"}
                        ]
                    },
                    "shadowColor": "rgba(59, 130, 246, 0.4)",
                    "shadowBlur": 10
                },
                "label": {
                    "show": True,
                    "position": "right",
                    "formatter": "{c} pts (Terpilih)",
                    "fontWeight": "bold",
                    "color": "#1e3a8a"
                }
            })
        else:
            series_data.append({
                "value": p,
                "itemStyle": {
                    "color": "#cbd5e1"
                },
                "label": {
                    "show": True,
                    "position": "right",
                    "formatter": "{c} pts",
                    "color": "#64748b"
                }
            })
            
    options = {
        "title": {
            "text": f"Leaderboard TELDA - Kuartal {selected_quarter}",
            "textStyle": {"fontSize": 14, "fontWeight": "bold", "color": "#1e293b"},
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}
        },
        "grid": {
            "left": "3%",
            "right": "15%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Total Points",
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#e2e8f0"}}
        },
        "yAxis": {
            "type": "category",
            "data": teldas,
            "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            "axisLabel": {"fontWeight": "bold", "color": "#475569"}
        },
        "series": [{
            "name": "Total Points",
            "type": "bar",
            "data": series_data,
            "barWidth": "60%",
        }]
    }
    
    st_echarts(options=options, height="350px")


def render_trend_chart(df: pd.DataFrame, selected_telda: str) -> None:
    """Render trend evaluation graph across quarters (G30)."""
    df_t = df[df["TELDA"] == selected_telda].copy()
    if df_t.empty:
        return
        
    df_t["QUARTER_SORT"] = df_t["QUARTER"].map(QUARTER_SORT_MAP).fillna(0)
    df_t = df_t.sort_values(by="QUARTER_SORT")
    
    quarters = df_t["QUARTER"].tolist()
    points = pd.to_numeric(df_t["TOTAL POINT"], errors='coerce').fillna(0).tolist()
    ranks = pd.to_numeric(df_t["RANK"], errors='coerce').fillna(8).tolist()
    
    options = {
        "title": {
            "text": f"Tren Performa {selected_telda} - Q1 s/d Q4",
            "textStyle": {"fontSize": 14, "fontWeight": "bold", "color": "#1e293b"},
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Total Points", "Rank (Peringkat)"],
            "top": "bottom"
        },
        "grid": {
            "left": "5%",
            "right": "5%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": quarters,
            "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            "axisLabel": {"fontWeight": "bold", "color": "#475569"}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Points",
                "min": 0,
                "max": 100,
                "splitLine": {"lineStyle": {"type": "dashed", "color": "#e2e8f0"}}
            },
            {
                "type": "value",
                "name": "Rank",
                "inverse": True,
                "min": 1,
                "max": 8,
                "splitNumber": 8,
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Total Points",
                "type": "line",
                "data": points,
                "smooth": True,
                "itemStyle": {"color": "#3b82f6"},
                "lineStyle": {"width": 3},
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
                "name": "Rank (Peringkat)",
                "type": "line",
                "yAxisIndex": 1,
                "data": ranks,
                "smooth": True,
                "itemStyle": {"color": "#f59e0b"},
                "lineStyle": {"width": 3, "type": "dashed"}
            }
        ]
    }
    
    st_echarts(options=options, height="350px")
