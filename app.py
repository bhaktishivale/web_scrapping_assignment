import streamlit as st
import subprocess
import sys
import os

st.set_page_config(
    page_title="Web Scraping Assignment",
    page_icon="🌐"
)

st.title("🌐 Web Scraping Assignment")
st.write("Run the web scraping ETL pipeline.")

if st.button("Run Scraper"):
    with st.spinner("Running scraper..."):
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True
        )

    if result.returncode == 0:
        st.success("Scraper completed successfully!")

        if result.stdout:
            st.subheader("Output")
            st.code(result.stdout)

    else:
        st.error("Scraper encountered an error.")

        if result.stderr:
            st.subheader("Error")
            st.code(result.stderr)

st.divider()

st.subheader("Generated Files")

for filename in [
    "output/final_dataset.csv",
    "output/summary_report.json"
]:
    if os.path.exists(filename):
        st.write(f"✅ `{filename}`")
    else:
        st.write(f"❌ `{filename}`")