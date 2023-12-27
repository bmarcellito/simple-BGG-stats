import googleapiclient.discovery
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build


@st.cache_data(max_entries=10)
def authenticate() -> googleapiclient.discovery.Resource:
    scopes = ['https://www.googleapis.com/auth/drive']
    private_key_id = st.secrets["private_key_id"]
    private_key = st.secrets["private_key"]
    client_email = st.secrets["client_email"]
    client_id = st.secrets["client_id"]
    service_account_info = {
        "type": "service_account",
        "project_id": "simple-bgg-stat-service-acc",
        "private_key_id": private_key_id,
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/simple-bgg-stat-sa%40simple-bgg-"
                                "stat-service-acc.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=scopes)
    service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    return service
