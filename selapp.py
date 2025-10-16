import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd

st.title("Selenium Web Extractor")

# Input URL
url = st.text_input("Enter URL to extract", "https://www.w3schools.com/html/html_tables.asp")

# Options to extract
extract_text = st.checkbox("Extract all text", value=True)
extract_tables = st.checkbox("Extract tables", value=True)

if st.button("Extract"):
    st.write(f"Opening {url} ...")

    # Setup Selenium
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # remove to see browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")
    
    if extract_text:
        text = soup.get_text(separator="\n")
        st.subheader("Page Text")
        st.text(text[:2000] + "\n...")  # showing first 2000 chars
    
    if extract_tables:
        tables = pd.read_html(html)
        st.subheader("Tables Found")
        for i, table in enumerate(tables):
            st.write(f"Table {i+1}")
            st.dataframe(table)
    
    st.success("Extraction Complete!")
    driver.quit()
