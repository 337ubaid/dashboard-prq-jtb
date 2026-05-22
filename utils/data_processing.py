import pandas as pd
import streamlit as st
import gspread
from typing import Any
from google.oauth2.service_account import Credentials
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

MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
}

def _clean_pivot_dataframe(
    pivot_df: pd.DataFrame, 
    index_col: str = 'FLAG_SCALING_MONTHLY_REVENUE', 
    add_total_col: bool = False,
    sort_by_total: bool = False
) -> pd.DataFrame:
    clean_columns = {}
    for col in pivot_df.columns:
        if col.startswith('_') and len(col) == 8:
            year = col[1:5]
            month = col[6:8]
            clean_columns[col] = f"{MONTH_MAP.get(month, month)} {year}"
        elif len(col) == 7 and col[4] == '-':
            year = col[0:4]
            month = col[5:7]
            clean_columns[col] = f"{MONTH_MAP.get(month, month)} {year}"
            
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

@st.cache_data(ttl=60)
def load_spreadsheet_data(worksheet_name: str = "LOOKER IMPACTFUL TELDA") -> pd.DataFrame:
    """Loads and caches data from Google Sheet using official gspread API with secrets-based service account."""
    try:
        sheet_url = st.secrets["spreadsheet"]["kpi_telda"]
    except KeyError:
        st.sidebar.error("Gagal memuat: `spreadsheet.kpi_telda` tidak ditemukan di secrets.toml.")
        return pd.DataFrame()
        
    if sheet_url:
        client_email = ""
        try:
            # 1. Define OAuth Scopes
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # 2. Get GCP Service Account credentials from Streamlit Secrets
            if "gcp_service_account" not in st.secrets:
                st.sidebar.error("Gagal memuat: `gcp_service_account` tidak ditemukan di secrets.toml.")
                return pd.DataFrame()
                
            creds_dict = dict(st.secrets["gcp_service_account"])
            client_email = creds_dict.get("client_email", "")
            
            # 3. Authenticate and authorize client
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            gc = gspread.authorize(creds)
            
            # 4. Open the Spreadsheet
            sh = gc.open_by_url(sheet_url.strip())
            
            # 5. Get the specific worksheet
            if worksheet_name and worksheet_name.strip() != "":
                ws = sh.worksheet(worksheet_name.strip())
            else:
                ws = sh.get_worksheet(0)
                
            # 6. Retrieve records and build DataFrame
            records = ws.get_all_records()
            if not records:
                st.sidebar.warning(f"Lembar kerja '{worksheet_name}' kosong.")
                return pd.DataFrame()
                
            df = pd.DataFrame(records)
            
            # Standardize column headers (remove leading/trailing spaces)
            df.columns = [col.strip() for col in df.columns]
            return df
        except gspread.exceptions.SpreadsheetNotFound:
            st.sidebar.error("Spreadsheet tidak ditemukan. Pastikan URL benar.")
        except gspread.exceptions.WorksheetNotFound:
            st.sidebar.error(f"Worksheet '{worksheet_name}' tidak ditemukan di spreadsheet tersebut.")
        except Exception as e:
            err_msg = str(e)
            if "PERMISSION_DENIED" in err_msg or "caller does not have permission" in err_msg or "403" in err_msg:
                st.sidebar.error(
                    f"**Akses Ditolak!** Pastikan spreadsheet Anda telah di-share (dibagikan) ke email Service Account berikut:\n"
                    f"`{client_email if client_email else 'email service account Anda'}`"
                )
            else:
                st.sidebar.error(f"Gagal memuat Google Sheet via gspread: {e}")
            
    return pd.DataFrame()


def clean_numeric_val(val: Any) -> float:
    """Clean numeric values from string placeholders, commas, and percentage signs."""
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    if val_str in ["-", "", "  - ", "n/a", "N/A"]:
        return 0.0
    
    val_str = val_str.replace('%', '').replace('Rp', '').replace(' ', '')
    
    if isinstance(val, (int, float)):
        return float(val)
        
    try:
        return float(val_str)
    except ValueError:
        # If float format is European (comma as decimal, dot as thousand separator)
        val_str = val_str.replace('.', '').replace(',', '.')
        try:
            return float(val_str)
        except ValueError:
            return 0.0


def find_column_by_prefix_and_suffix(df: pd.DataFrame, prefix: str, suffix: str) -> str | None:
    """Safely find a column header in the dataframe that matches a metric prefix and suffix."""
    p_clean = prefix.strip().upper()
    s_clean = suffix.strip().upper()
    
    # Try exact matches first
    for col in df.columns:
        c_upper = col.strip().upper()
        if c_upper == f"{p_clean} - {s_clean}" or c_upper == f"{p_clean}-{s_clean}" or c_upper == f"{p_clean} -{s_clean}" or c_upper == f"{p_clean}- {s_clean}":
            return col
            
    # Substring search if direct fails
    for col in df.columns:
        c_upper = col.strip().upper()
        if p_clean in c_upper and s_clean in c_upper:
            return col
            
    return None


def build_scorecard_table(df_row: pd.DataFrame, mapping_dict: dict[str, str]) -> pd.DataFrame:
    """Build the scorecard table for the single filtered row based on the mapping dictionary."""
    rows_data = []
    
    if df_row.empty:
        return pd.DataFrame()
        
    for label, prefix in mapping_dict.items():
        target_col = find_column_by_prefix_and_suffix(df_row, prefix, "TARGET")
        
        # Try different realisasi spellings
        real_col = None
        for r_suffix in ["REALIASASI", "REALISASI"]:
            real_col = find_column_by_prefix_and_suffix(df_row, prefix, r_suffix)
            if real_col:
                break
                
        ach_col = find_column_by_prefix_and_suffix(df_row, prefix, "ACH")
        point_col = find_column_by_prefix_and_suffix(df_row, prefix, "POINT")
        
        target_raw = df_row[target_col].values[0] if target_col and target_col in df_row.columns else 0.0
        realisasi_raw = df_row[real_col].values[0] if real_col and real_col in df_row.columns else 0.0
        ach_raw = df_row[ach_col].values[0] if ach_col and ach_col in df_row.columns else 0.0
        point_raw = df_row[point_col].values[0] if point_col and point_col in df_row.columns else 0.0
        
        target = clean_numeric_val(target_raw)
        realisasi = clean_numeric_val(realisasi_raw)
        
        if ach_raw and str(ach_raw).strip() not in ["-", ""]:
            ach = clean_numeric_val(ach_raw)
        else:
            ach = (realisasi / target * 100) if target > 0 else 0.0
            
        point = clean_numeric_val(point_raw)
        
        rows_data.append({
            "METRIC": label,
            "TARGET": target,
            "REALISASI": realisasi,
            "ACHIEVEMENT": ach,
            "POINT": point
        })
        
    res_df = pd.DataFrame(rows_data)
    if not res_df.empty:
        res_df.set_index("METRIC", inplace=True)
    return res_df


def load_and_clean_data() -> pd.DataFrame:
    """Load Google Sheet spreadsheet data and fall back to local CSV if unavailable."""
    df = load_spreadsheet_data()
    
    if df.empty:
        import os
        local_path = "lokeer impactfull.csv"
        if os.path.exists(local_path):
            try:
                df = pd.read_csv(local_path)
                if df.columns[0].strip() == "" or "Unnamed" in df.columns[0]:
                    df = df.iloc[:, 1:]
            except Exception as e:
                st.sidebar.error(f"Gagal memuat fallback CSV lokal: {e}")
                
    if not df.empty:
        df.columns = [col.strip() for col in df.columns]
        if "TELDA" in df.columns:
            df["TELDA"] = df["TELDA"].astype(str).str.strip().str.upper()
        if "QUARTER" in df.columns:
            df["QUARTER"] = df["QUARTER"].astype(str).str.strip().str.upper()
            
    return df
