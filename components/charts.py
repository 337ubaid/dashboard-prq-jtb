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


def render_leaderboard_chart(df: pd.DataFrame, selected_quarter: str | list[str], selected_telda: str | list[str]) -> None:
    """Render standard leaderboard bar chart using ECharts (G30)."""
    # Normalize inputs to list of uppercase strings for robust comparison (G3)
    quarters = [selected_quarter.upper()] if isinstance(selected_quarter, str) else [q.upper() for q in selected_quarter]
    teldas_to_highlight = [selected_telda.upper()] if isinstance(selected_telda, str) else [t.upper() for t in selected_telda]
    
    df_q = df[df["QUARTER"].str.upper().isin(quarters)].copy()
    if df_q.empty:
        return
        
    df_q["TOTAL POINT"] = pd.to_numeric(df_q["TOTAL POINT"], errors='coerce').fillna(0)
    
    # Group by TELDA and average the total points across selected quarters
    df_grouped = df_q.groupby("TELDA")["TOTAL POINT"].mean().reset_index()
    df_grouped = df_grouped.sort_values(by="TOTAL POINT", ascending=True)
    
    teldas = df_grouped["TELDA"].tolist()
    points = df_grouped["TOTAL POINT"].round(2).tolist()
    
    series_data = []
    for t, p in zip(teldas, points):
        if t.upper() in teldas_to_highlight:
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
            
    quarters_str = ", ".join(quarters)
    options = {
        "title": {
            "text": f"Leaderboard TELDA - Kuartal {quarters_str}",
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


def render_trend_chart(df: pd.DataFrame, selected_telda: str | list[str]) -> None:
    """Render trend evaluation graph across quarters (G30)."""
    teldas = [selected_telda.upper()] if isinstance(selected_telda, str) else [t.upper() for t in selected_telda]
    
    df_t = df[df["TELDA"].str.upper().isin(teldas)].copy()
    if df_t.empty:
        return
        
    df_t["QUARTER_SORT"] = df_t["QUARTER"].map(QUARTER_SORT_MAP).fillna(0)
    
    # Pre-process columns for averaging
    df_t["TOTAL POINT"] = pd.to_numeric(df_t["TOTAL POINT"], errors='coerce').fillna(0)
    df_t["RANK"] = pd.to_numeric(df_t["RANK"], errors='coerce').fillna(8)
    
    # Group by Quarter to average performance of selected teldas
    df_grouped = df_t.groupby(["QUARTER_SORT", "QUARTER"]).agg({
        "TOTAL POINT": "mean",
        "RANK": "mean"
    }).reset_index()
    df_grouped = df_grouped.sort_values(by="QUARTER_SORT")
    
    quarters = df_grouped["QUARTER"].tolist()
    points = df_grouped["TOTAL POINT"].round(2).tolist()
    ranks = df_grouped["RANK"].round(1).tolist()
    
    teldas_str = ", ".join(teldas) if len(teldas) <= 3 else f"{len(teldas)} TELDA"
    
    options = {
        "title": {
            "text": f"Tren Performa {teldas_str} - Q1 s/d Q4",
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

