import pandas as pd
from data.bq_client import query_data, DATASET
from utils.helpers import format_short_number
from data.processing import layanan_dict

def get_filter_options() -> dict[str, list]:
    """Mengambil opsi filter yang tersedia dari BigQuery."""
    def fetch_distinct(col_expr, alias, table):
        query = f"SELECT DISTINCT {col_expr} as {alias} FROM `{table}` WHERE {col_expr} IS NOT NULL ORDER BY {alias}"
        df = query_data(query)
        return df[alias].tolist() if not df.empty else []

    table = f"{DATASET}.POTS_JOINED"
    
    return {
        "years": fetch_distinct("YEAR_ID", "val", table),
        "flags": fetch_distinct("IFNULL(FLAG_SCALING_MONTHLY_REVENUE, 'Uncategorized')", "val", table),
        "subsegmen": fetch_distinct("SUBSEGMEN_HO", "val", table),
        "bam": fetch_distinct("NAMA_BAM", "val", table),
        "telda": fetch_distinct("TELDA", "val", table),
        "sto": fetch_distinct("STO", "val", table)
    }

def _build_where_clause(filters: dict[str, any]) -> str:
    where_clauses = []
    
    mapping = {
        "years": ("YEAR_ID IN ({})", False),
        "flags": ("IFNULL(FLAG_SCALING_MONTHLY_REVENUE, 'Uncategorized') IN ({})", True),
        "subsegmen": ("SUBSEGMEN_HO IN ({})", True),
        "bam": ("NAMA_BAM IN ({})", True),
        "telda": ("TELDA IN ({})", True),
        "sto": ("STO IN ({})", True),
    }
    
    for key, (clause_tpl, is_string) in mapping.items():
        vals = filters.get(key, [])
        if vals:
            if is_string:
                vals_str = ", ".join([f"'{v}'" for v in vals])
            else:
                vals_str = ", ".join([str(v) for v in vals])
            where_clauses.append(clause_tpl.format(vals_str))
            
    nipnas = filters.get("nipnas_search", "").strip()
    if nipnas:
        where_clauses.append(f"NIPNAS_TEMP LIKE '%{nipnas}%'")
        
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

def _clean_pivot_dataframe(
    pivot_df: pd.DataFrame, 
    index_col: str = 'FLAG_SCALING_MONTHLY_REVENUE', 
    add_total_col: bool = False,
    sort_by_total: bool = False
) -> pd.DataFrame:
    clean_columns = {}
    for col in pivot_df.columns:
        if col.startswith('_') and len(col) == 8:
            clean_columns[col] = col[1:5] + '-' + col[6:]
            
    if clean_columns:
        pivot_df.rename(columns=clean_columns, inplace=True)
    
    pivot_df.set_index(index_col, inplace=True)
    pivot_df = pivot_df.fillna(0)
    
    if add_total_col:
        pivot_df['Total'] = pivot_df.sum(axis=1)
        
    if sort_by_total and 'Total' in pivot_df.columns:
        pivot_df = pivot_df.sort_values(by='Total', ascending=False)
        
    pivot_df.loc['Total'] = pivot_df.sum()
    
    return pivot_df

def _extract_echarts_data(pivot_df: pd.DataFrame) -> tuple[list[str], list[dict]]:
    x_axis_data = pivot_df.columns.tolist()
    total_data_raw = pivot_df.loc['Total'].tolist()
    
    formatted_data = []
    for val in total_data_raw:
        formatted_data.append({
            "value": val,
            "label": {
                "show": True,
                "position": "top",
                "formatter": format_short_number(val)
            }
        })
        
    series_data = [{
        "name": "Total Revenue",
        "type": "line",
        "data": formatted_data,
        "smooth": True,
        "itemStyle": {"color": "#1f77b4"}
    }]
    return x_axis_data, series_data

def get_pivoted_data_from_bq(filters: dict[str, any]) -> tuple[pd.DataFrame | None, list[str] | None, list[dict] | None]:
    """
    Melakukan query agregasi dan pivot langsung di sisi BigQuery.
    Jika filter dibiarkan kosong, sistem akan otomatis memilih semua (select all).
    """
    where_sql = _build_where_clause(filters)
    periods = _get_available_periods(where_sql)
    
    if not periods:
        return None, None, None
        
    pivot_df = _execute_pivot_query(where_sql, periods)
    
    if pivot_df.empty:
        return None, None, None
        
    pivot_df = _clean_pivot_dataframe(pivot_df, index_col='FLAG_SCALING_MONTHLY_REVENUE')
    x_axis_data, series_data = _extract_echarts_data(pivot_df)
    
    return pivot_df, x_axis_data, series_data

def _build_layanan_case_statement(mapping_dict: dict[str, list[str]]) -> str:
    case_sql = "CASE\n"
    for category, values in mapping_dict.items():
        if values:
            values_str = ", ".join([f"'{v}'" for v in values])
            case_sql += f"        WHEN GROUP5 IN ({values_str}) THEN '{category}'\n"
    case_sql += "        ELSE 'Others'\n    END"
    return case_sql

def get_layanan_pivoted_data_from_bq(filters: dict[str, any]) -> pd.DataFrame | None:
    """
    Melakukan query agregasi dan pivot layanan berdasarkan mapping GROUP5 di BigQuery.
    """
    where_sql = _build_where_clause(filters)
    periods = _get_available_periods(where_sql)
    
    if not periods:
        return None
        
    periods_in_clause = ", ".join([f"'{p}'" for p in periods])
    layanan_case = _build_layanan_case_statement(layanan_dict)
    
    pivot_query = f"""
    SELECT * FROM (
      SELECT {layanan_case} as Layanan,
             CONCAT(CAST(YEAR_ID AS STRING), '-', LPAD(CAST(MONTH_ID AS STRING), 2, '0')) as Periode,
             REVENUE
      FROM `{DATASET}.POTS_JOINED`
      {where_sql}
    )
    PIVOT (
      SUM(REVENUE) FOR Periode IN ({periods_in_clause})
    )
    """
    pivot_df = query_data(pivot_query)
    
    if pivot_df.empty:
        return None
        
    pivot_df = _clean_pivot_dataframe(
        pivot_df, 
        index_col='Layanan', 
        add_total_col=True, 
        sort_by_total=True
    )
    
    return pivot_df

def get_top_bottom_pelanggan_from_bq(filters: dict[str, any], n: int = 10) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """
    Mengambil data Top N dan Bottom N NIPNAS_TEMP berdasarkan total REVENUE.
    """
    where_sql = _build_where_clause(filters)
    
    query_top = f"""
        SELECT NIPNAS_TEMP, SUM(REVENUE) as REVENUE
        FROM `{DATASET}.POTS_JOINED`
        {where_sql}
        GROUP BY NIPNAS_TEMP
        ORDER BY REVENUE DESC
        LIMIT {n}
    """
    
    query_bottom = f"""
        SELECT NIPNAS_TEMP, SUM(REVENUE) as REVENUE
        FROM `{DATASET}.POTS_JOINED`
        {where_sql}
        GROUP BY NIPNAS_TEMP
        ORDER BY REVENUE ASC
        LIMIT {n}
    """
    
    top_df = query_data(query_top)
    bottom_df = query_data(query_bottom)
    
    if top_df.empty and bottom_df.empty:
        return None, None
        
    if not top_df.empty:
        top_df.index = range(1, len(top_df) + 1)
        top_df.index.name = 'Rank'
        
    if not bottom_df.empty:
        bottom_df.index = range(1, len(bottom_df) + 1)
        bottom_df.index.name = 'Rank'
        
    return top_df, bottom_df


