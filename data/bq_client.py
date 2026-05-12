import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

DATASET = st.secrets["bigquery"]["dataset"]

@st.cache_resource
def get_bq_client():
    """
    Initialize and cache BigQuery Client using Streamlit secrets.
    """
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    return client

@st.cache_data(ttl=600)
def query_data(query: str) -> pd.DataFrame:
    """
    Run a BigQuery query and return results as Pandas DataFrame.
    Results are cached for 10 minutes to save costs.
    """
    client = get_bq_client()
    query_job = client.query(query)
    return query_job.to_dataframe()
