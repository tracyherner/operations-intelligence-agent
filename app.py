import streamlit as st

st.title("AI Manager Decision System")

query = st.text_input("Ask a management question:")

if query:
    st.write(f"Processing: {query}")