import streamlit as st

st.set_page_config(
    page_title="PRQ Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main() -> None:
    st.title("📊 PRQ Dashboard Main Page")
    st.write("Selamat datang di PRQ Dashboard. Silakan pilih menu di sidebar untuk melihat data.")
    
    st.info("💡 Pilih menu di sidebar sebelah kiri.")

if __name__ == "__main__":
    main()
