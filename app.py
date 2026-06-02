import streamlit as st
from utils.helpers import setup_page

setup_page("PRQ Dashboard")

def main() -> None:
    st.title("📊 PRQ Dashboard Main Page")
    st.write("Selamat datang di PRQ Dashboard. Silakan pilih menu di sidebar untuk melihat data.")
    
    st.info("💡 Pilih menu di sidebar sebelah kiri.")

if __name__ == "__main__":
    main()

