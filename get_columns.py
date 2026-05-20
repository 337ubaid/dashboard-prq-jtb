import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery

# Ambil secrets
creds_info = st.secrets["gcp_service_account"]
dataset = st.secrets["bigquery"]["dataset"]

credentials = service_account.Credentials.from_service_account_info(creds_info)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

table_id = f"{client.project}.{dataset}.POTS_JOINED"
table = client.get_table(table_id)

print("--- Kolom di POTS_JOINED ---")
for field in table.schema:
    print(f"- {field.name} ({field.field_type})")
