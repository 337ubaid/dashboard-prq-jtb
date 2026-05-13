import pandas as pd
from data.bq_client import query_data, DATASET

def get_filter_options() -> tuple[list[int], list[str]]:
    """Mengambil opsi filter (Tahun dan Flag Revenue) yang tersedia dari BigQuery."""
    query_years = f"""
        SELECT DISTINCT YEAR_ID 
        FROM `{DATASET}.POTS_JOINED` 
        WHERE YEAR_ID IS NOT NULL
        ORDER BY YEAR_ID
    """
    years_df = query_data(query_years)
    years = years_df['YEAR_ID'].tolist()
    
    query_flags = f"""
        SELECT DISTINCT IFNULL(FLAG_SCALING_MONTHLY_REVENUE, 'Uncategorized') as FLAG
        FROM `{DATASET}.POTS_JOINED`
        ORDER BY FLAG
    """
    flags_df = query_data(query_flags)
    flags = flags_df['FLAG'].tolist()
    
    return years, flags

def _build_where_clause(selected_years: list[int], selected_flags: list[str]) -> str:
    where_clauses = []
    
    if selected_years:
        years_str = ", ".join([str(y) for y in selected_years])
        where_clauses.append(f"YEAR_ID IN ({years_str})")
        
    if selected_flags:
        flags_str = ", ".join([f"'{f}'" for f in selected_flags])
        where_clauses.append(f"IFNULL(FLAG_SCALING_MONTHLY_REVENUE, 'Uncategorized') IN ({flags_str})")
        
    if where_clauses:
        return "WHERE " + " AND ".join(where_clauses)
    return ""

def _get_available_periods(where_sql: str) -> list[str]:
    periods_query = f"""
        SELECT DISTINCT CONCAT(CAST(YEAR_ID AS STRING), '-', LPAD(CAST(MONTH_ID AS STRING), 2, '0')) as Periode
        FROM `{DATASET}.POTS_JOINED`
        {where_sql}
        ORDER BY Periode
    """
    periods_df = query_data(periods_query)
    
    if periods_df.empty:
        return []
        
    return periods_df['Periode'].tolist()

def _execute_pivot_query(where_sql: str, periods: list[str]) -> pd.DataFrame:
    if not periods:
        return pd.DataFrame()

    periods_in_clause = ", ".join([f"'{p}'" for p in periods])
    
    pivot_query = f"""
    SELECT * FROM (
      SELECT IFNULL(FLAG_SCALING_MONTHLY_REVENUE, 'Uncategorized') as FLAG_SCALING_MONTHLY_REVENUE,
             CONCAT(CAST(YEAR_ID AS STRING), '-', LPAD(CAST(MONTH_ID AS STRING), 2, '0')) as Periode,
             REVENUE
      FROM `{DATASET}.POTS_JOINED`
      {where_sql}
    )
    PIVOT (
      SUM(REVENUE) FOR Periode IN ({periods_in_clause})
    )
    """
    return query_data(pivot_query)

def _clean_pivot_dataframe(pivot_df: pd.DataFrame) -> pd.DataFrame:
    clean_columns = {}
    for col in pivot_df.columns:
        if col.startswith('_') and len(col) == 8:
            clean_columns[col] = col[1:5] + '-' + col[6:]
            
    if clean_columns:
        pivot_df.rename(columns=clean_columns, inplace=True)
    
    pivot_df.set_index('FLAG_SCALING_MONTHLY_REVENUE', inplace=True)
    pivot_df = pivot_df.fillna(0)
    pivot_df.loc['Total'] = pivot_df.sum()
    
    return pivot_df

def _extract_echarts_data(pivot_df: pd.DataFrame) -> tuple[list[str], list[dict]]:
    x_axis_data = pivot_df.columns.tolist()
    total_data = pivot_df.loc['Total'].tolist()
    series_data = [{
        "name": "Total Revenue",
        "type": "line",
        "data": total_data,
        "smooth": True
    }]
    return x_axis_data, series_data

def get_pivoted_data_from_bq(selected_years: list[int], selected_flags: list[str]) -> tuple[pd.DataFrame | None, list[str] | None, list[dict] | None]:
    """
    Melakukan query agregasi dan pivot langsung di sisi BigQuery.
    Jika filter dibiarkan kosong, sistem akan otomatis memilih semua (select all).
    """
    where_sql = _build_where_clause(selected_years, selected_flags)
    periods = _get_available_periods(where_sql)
    
    if not periods:
        return None, None, None
        
    pivot_df = _execute_pivot_query(where_sql, periods)
    
    if pivot_df.empty:
        return None, None, None
        
    pivot_df = _clean_pivot_dataframe(pivot_df)
    x_axis_data, series_data = _extract_echarts_data(pivot_df)
    
    return pivot_df, x_axis_data, series_data
