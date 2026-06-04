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

def get_layanan_pelanggan_pivoted_data_from_bq(filters: dict[str, any]) -> pd.DataFrame | None:
    """
    Melakukan query agregasi dan pivot jumlah pelanggan per layanan berdasarkan mapping GROUP5 di BigQuery.
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
             NIPNAS_TEMP
      FROM `{DATASET}.POTS_JOINED`
      {where_sql}
    )
    PIVOT (
      COUNT(DISTINCT NIPNAS_TEMP) FOR Periode IN ({periods_in_clause})
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
    """Clean numeric values from string placeholders, currency symbols, and any thousand/decimal separators."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
        
    val_str = str(val).strip()
    if val_str in ["-", "", "  - ", "n/a", "N/A"]:
        return 0.0
        
    # Remove common non-numeric formatting characters
    val_str = val_str.replace('%', '').replace('Rp', '').replace(' ', '')
    
    # Try parsing directly
    try:
        return float(val_str)
    except ValueError:
        pass
        
    # Handle thousand and decimal separators:
    # 1. Standard English/US format with commas as thousand separators and dot as decimal (e.g. 1,234,567.89 or 1,234,567)
    # 2. European/Indonesian format with dots as thousand separators and comma as decimal (e.g. 1.234.567,89 or 1.234.567)
    
    has_comma = ',' in val_str
    has_dot = '.' in val_str
    
    if has_comma and has_dot:
        comma_idx = val_str.find(',')
        dot_idx = val_str.find('.')
        if comma_idx < dot_idx:
            # Comma comes first, so comma is thousand separator, dot is decimal (US format)
            val_str = val_str.replace(',', '')
        else:
            # Dot comes first, so dot is thousand separator, comma is decimal (Indonesian/European format)
            val_str = val_str.replace('.', '').replace(',', '.')
    elif has_comma:
        # Only commas are present (e.g., 1,898,561,512 or 12,5)
        # Check if the comma is a thousand separator or decimal separator
        # In typical business metrics, if there are multiple commas, or if the single comma is followed by exactly 3 digits
        # and we are dealing with large numbers, it is a thousand separator.
        temp_str = val_str.replace(',', '')
        try:
            parts = val_str.split(',')
            if len(parts) == 2 and len(parts[1]) != 3:
                return float(val_str.replace(',', '.'))
            else:
                return float(temp_str)
        except ValueError:
            # Fallback to replacing comma with dot
            try:
                return float(val_str.replace(',', '.'))
            except ValueError:
                return 0.0
    elif has_dot:
        # Only dots are present (e.g., 1.898.561.512 or 12.5)
        # If there are multiple dots, they are thousand separators
        if val_str.count('.') > 1:
            val_str = val_str.replace('.', '')
            
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


@st.cache_data(ttl=60)
def load_monthly_impactful_data() -> list[list[str]]:
    """Loads and caches monthly data from 'Impactful Telda New' sheet, falling back to data/sheet_raw.json."""
    try:
        sheet_url = st.secrets["spreadsheet"]["kpi_telda"]
    except KeyError:
        sheet_url = None
        
    if sheet_url:
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            gc = gspread.authorize(creds)
            sh = gc.open_by_url(sheet_url.strip())
            ws = sh.worksheet("Impactful Telda New")
            return ws.get_all_values()
        except Exception:
            pass
            
    # Fallback to local raw JSON if sheet fetch fails
    import os
    import json
    local_json_path = os.path.join("data", "sheet_raw.json")
    if os.path.exists(local_json_path):
        try:
            with open(local_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    return []


# ==========================================
# Named Constants for 2026 Monthly KPI Scoring and Layout (G25, P2)
# ==========================================
KPI_WEIGHTS: dict[str, float] = {
    "REV SME - POTS": 35.0,
    "REV SME - NON POTS": 5.0,
    "REV GOV": 5.0,
    "REV PS": 5.0,
    "REV SOE": 5.0,
    "HSI ALL SEGMENT": 20.0,
    "LTS": 3.0,
    "BW": 5.0,
    "OCA": 2.0,
    "NETMONK": 3.0,
    "EAZY": 3.0,
    "PIJAR SEKOLAH": 2.0,
    "C3MR": 5.0,
    "VISIT": 2.0
}

TELDA_REGIONS: list[str] = [
    "BATU", "BLITAR", "BOJONEGORO", "KEDIRI", 
    "MADIUN", "MALANG", "NGANJUK", "PONOROGO"
]

MONTHS_2026: list[str] = [f"2026{m:02d}" for m in range(1, 13)]

MONTHLY_HEADER_INDICES: list[int] = [
    2, 12, 22, 32, 42, 52, 62, 72, 82, 92, 102, 112, 122, 132, 142, 152, 162, 172, 182
]

METRICS_MAPPING: dict[int, str] = {
    1: "REV SME - POTS",
    2: "REV SME - NON POTS",
    3: "REV GOV",
    4: "REV PS",
    5: "REV SOE",
    6: "TABEL HSI + TABEL WMS",
    7: "BW",
    8: "OCA",
    9: "NETMONK",
    10: "EAZY",
    11: "PIJAR SEKOLAH",
    12: "DO CTO",
    13: "REAL SALES",
    14: "TABEL VISIT & PROFILING",
    15: "C3MR BAYAR",
    16: "C3MR BILL"
}

METRIC_HEADERS_MAPPING: dict[int, list[int]] = {
    1: [2],
    2: [12],
    3: [22],
    4: [32],
    5: [42],
    6: [52, 62],  # Combines HSI (52) and WMS (62)
    7: [72],
    8: [82],
    9: [92],
    10: [102],
    11: [112],
    12: [122],
    13: [132],
    14: [142, 152, 162],  # Combines VISIT (142), PROF_SME (152), PROF_LEGS (162)
    15: [172],
    16: [182]
}

STANDARD_C3MR_TARGET: float = 98.0
ACHIEVEMENT_CAP: float = 110.0
LEFT_START_COL: int = 2
RIGHT_START_COL: int = 17


def load_and_clean_monthly_data() -> pd.DataFrame:
    """Parses raw monthly grid data into a normalized, consolidated DataFrame (G30)."""
    raw_data: list[list[str]] = load_monthly_impactful_data()
    if not raw_data:
        return pd.DataFrame()
        
    # Initialize normalized rows dictionary mapping (TELDA, MONTH) -> row values
    db: dict[tuple[str, str], dict[str, float]] = {}
    for w in TELDA_REGIONS:
        for m in MONTHS_2026:
            db[(w, m)] = {}
            
    # Parse Tables 1 to 16
    for t_idx, headers in METRIC_HEADERS_MAPPING.items():
        metric_name: str = METRICS_MAPPING[t_idx]
        
        for offset, w in enumerate(TELDA_REGIONS):
            if metric_name == "TABEL VISIT & PROFILING":
                # Special parsing logic for Visit & Profiling
                # Target is always 5.0
                # Realisasi = 0.5 * VISIT + 0.25 * PROF_SME + 0.25 * PROF_LEGS
                visit_real = [0.0] * len(MONTHS_2026)
                sme_real = [0.0] * len(MONTHS_2026)
                legs_real = [0.0] * len(MONTHS_2026)
                
                for idx, h in enumerate(headers):
                    row_idx: int = h + 1 + offset
                    if row_idx >= len(raw_data):
                        continue
                    r_data: list[str] = [cell.strip() for cell in raw_data[row_idx]]
                    
                    for m_idx, m in enumerate(MONTHS_2026):
                        r_col: int = RIGHT_START_COL + m_idx
                        real_val: float = clean_numeric_val(r_data[r_col]) if r_col < len(r_data) else 0.0
                        if idx == 0:
                            visit_real[m_idx] = real_val
                        elif idx == 1:
                            sme_real[m_idx] = real_val
                        elif idx == 2:
                            legs_real[m_idx] = real_val
                            
                for m_idx, m in enumerate(MONTHS_2026):
                    db[(w, m)][f"{metric_name} - TARGET"] = 5.0
                    db[(w, m)][f"{metric_name} - REALIASASI"] = (
                        0.5 * visit_real[m_idx] +
                        0.25 * sme_real[m_idx] +
                        0.25 * legs_real[m_idx]
                    )
            else:
                for h in headers:
                    row_idx: int = h + 1 + offset
                    if row_idx >= len(raw_data):
                        continue
                    r_data: list[str] = [cell.strip() for cell in raw_data[row_idx]]
                    
                    for m_idx, m in enumerate(MONTHS_2026):
                        l_col: int = LEFT_START_COL + m_idx
                        r_col: int = RIGHT_START_COL + m_idx
                        
                        target_val: float = clean_numeric_val(r_data[l_col]) if l_col < len(r_data) else 0.0
                        real_val: float = clean_numeric_val(r_data[r_col]) if r_col < len(r_data) else 0.0
                        
                        db[(w, m)][f"{metric_name} - TARGET"] = db[(w, m)].get(f"{metric_name} - TARGET", 0.0) + target_val
                        db[(w, m)][f"{metric_name} - REALIASASI"] = db[(w, m)].get(f"{metric_name} - REALIASASI", 0.0) + real_val
                        
    # Transform database to a list of rows
    final_rows: list[dict[str, Any]] = []
    for (w, m), data in db.items():
        row_dict: dict[str, Any] = {
            "TELDA": w,
            "MONTH": m
        }
        
        for t_idx in range(1, 17):
            metric_name: str = METRICS_MAPPING[t_idx]
            
            # Skip TARGET for DO CTO, REAL SALES, C3MR BAYAR, and C3MR BILL
            if metric_name not in ["DO CTO", "REAL SALES", "C3MR BAYAR", "C3MR BILL"]:
                row_dict[f"{metric_name} - TARGET"] = data.get(f"{metric_name} - TARGET", 0.0)
                
            row_dict[f"{metric_name} - REALIASASI"] = data.get(f"{metric_name} - REALIASASI", 0.0)
            
        final_rows.append(row_dict)
        
    df_result: pd.DataFrame = pd.DataFrame(final_rows)
    return df_result
