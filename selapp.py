import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import tempfile

st.set_page_config(layout="wide")
st.title("🌐 Playwright Mini-Browser & Web Extractor")

# ---------------- Sidebar ----------------
st.sidebar.header("Settings")
extract_text = st.sidebar.checkbox("Extract Text", True)
extract_tables = st.sidebar.checkbox("Extract Tables", True)
extract_links = st.sidebar.checkbox("Extract Links", True)
extract_images = st.sidebar.checkbox("Extract Image URLs", False)
custom_selector = st.sidebar.text_input("Custom CSS/XPath Selector (optional)", "")

# ---------------- Session State ----------------
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = -1
if 'current_url' not in st.session_state:
    st.session_state.current_url = "https://www.w3schools.com/html/html_tables.asp"

# ---------------- Navigation Functions ----------------
def navigate(url):
    st.session_state.history = st.session_state.history[:st.session_state.current_index+1]
    st.session_state.history.append(url)
    st.session_state.current_index += 1
    st.session_state.current_url = url

def go_back():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.current_url = st.session_state.history[st.session_state.current_index]

def go_forward():
    if st.session_state.current_index < len(st.session_state.history)-1:
        st.session_state.current_index += 1
        st.session_state.current_url = st.session_state.history[st.session_state.current_index]

# ---------------- Navigation Buttons ----------------
col1, col2, col3, col4 = st.columns([1,1,2,6])
with col1:
    if st.button("⬅ Back"):
        go_back()
with col2:
    if st.button("Forward ➡"):
        go_forward()
with col3:
    url_input = st.text_input("Enter URL", st.session_state.current_url)
    if st.button("Go"):
        navigate(url_input)
with col4:
    st.write(f"Current URL: {st.session_state.current_url}")

# ---------------- Playwright Extraction ----------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(st.session_state.current_url)
    page.wait_for_timeout(2000)  # wait for JS

    # Screenshot
    screenshot_path = tempfile.NamedTemporaryFile(suffix=".png").name
    page.screenshot(path=screenshot_path)
    st.image(screenshot_path, caption="Page Screenshot", use_column_width=True)

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    # ---------------- Extract Text ----------------
    if extract_text:
        text = soup.get_text(separator="\n")
        with st.expander("Page Text"):
            st.text(text[:5000] + "\n...")

    # ---------------- Extract Tables ----------------
    if extract_tables:
        try:
            tables = pd.read_html(html)
            st.subheader("Tables Found")
            for i, table in enumerate(tables):
                st.write(f"Table {i+1}")
                st.dataframe(table)
                st.download_button(f"Download Table {i+1} CSV", table.to_csv(index=False), f"table_{i+1}.csv", "text/csv")
        except:
            st.warning("No tables found.")

    # ---------------- Extract Links (Clickable) ----------------
    if extract_links:
        links = [(a.get("href"), a.text) for a in soup.find_all("a") if a.get("href")]
        st.subheader("Links Found")
        for href, text_link in links:
            if st.button(f"{text_link}"):
                if href.startswith("http"):
                    navigate(href)
                else:
                    base_url = "/".join(st.session_state.current_url.split("/")[:3])
                    navigate(base_url + href)

    # ---------------- Extract Images ----------------
    if extract_images:
        images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
        st.subheader("Images Found")
        st.write(images)
        if images:
            img_df = pd.DataFrame(images, columns=["Image URLs"])
            st.download_button("Download Image URLs CSV", img_df.to_csv(index=False), "images.csv", "text/csv")

    # ---------------- Custom Selector ----------------
    if custom_selector:
        st.subheader("Custom Selector Results")
        try:
            elements = page.query_selector_all(custom_selector)
            custom_data = [el.inner_text().strip() for el in elements if el.inner_text().strip()]
            st.write(custom_data)
            if custom_data:
                custom_df = pd.DataFrame(custom_data, columns=["Custom Extract"])
                st.download_button("Download Custom Extract CSV", custom_df.to_csv(index=False), "custom.csv", "text/csv")
        except Exception as e:
            st.error(f"Error with custom selector: {e}")

    st.success("Extraction Complete ✅")
    browser.close()
