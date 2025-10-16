import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import tempfile

st.set_page_config(layout="wide")
st.title("🕸️ Selenium Web Extractor / Mini Browser")

# --- Sidebar options ---
st.sidebar.header("Extraction Settings")
url_input = st.sidebar.text_input("Enter URL", "https://www.w3schools.com/html/html_tables.asp")
extract_text = st.sidebar.checkbox("Extract Text", value=True)
extract_tables = st.sidebar.checkbox("Extract Tables", value=True)
extract_links = st.sidebar.checkbox("Extract Links", value=False)
extract_images = st.sidebar.checkbox("Extract Image URLs", value=False)

# Navigation buttons
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = -1

def navigate(url):
    st.session_state.history = st.session_state.history[:st.session_state.current_index+1]
    st.session_state.history.append(url)
    st.session_state.current_index += 1

def go_back():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        return st.session_state.history[st.session_state.current_index]
    return None

def go_forward():
    if st.session_state.current_index < len(st.session_state.history)-1:
        st.session_state.current_index += 1
        return st.session_state.history[st.session_state.current_index]
    return None

# Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Back"):
        url_input = go_back()
with col2:
    if st.button("Forward"):
        url_input = go_forward()
with col3:
    if st.button("Go"):
        navigate(url_input)

if url_input:
    st.info(f"Loading: {url_input}")

    # Setup Selenium (headless for Streamlit Cloud)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url_input)
        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")
        
        # Extract Text
        if extract_text:
            text = soup.get_text(separator="\n")
            st.subheader("Page Text")
            st.text(text[:3000] + "\n...")  # first 3000 chars
        
        # Extract Tables
        if extract_tables:
            tables = pd.read_html(html)
            st.subheader("Tables Found")
            for i, table in enumerate(tables):
                st.write(f"Table {i+1}")
                st.dataframe(table)
                # Download as CSV
                csv = table.to_csv(index=False)
                st.download_button(f"Download Table {i+1} CSV", csv, f"table_{i+1}.csv", "text/csv")
        
        # Extract Links
        if extract_links:
            links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
            st.subheader("Links Found")
            st.write(links)
            links_df = pd.DataFrame(links, columns=["Links"])
            st.download_button("Download Links CSV", links_df.to_csv(index=False), "links.csv", "text/csv")
        
        # Extract Images
        if extract_images:
            images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
            st.subheader("Images Found")
            st.write(images)
            img_df = pd.DataFrame(images, columns=["Image URLs"])
            st.download_button("Download Image URLs CSV", img_df.to_csv(index=False), "images.csv", "text/csv")
        
        st.success("Extraction Complete ✅")
        
    except Exception as e:
        st.error(f"Error loading page: {e}")
    finally:
        driver.quit()
