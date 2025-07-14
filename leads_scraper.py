import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import tempfile
from datetime import datetime
import socket

# -------------------------------------
# Config
# -------------------------------------
SERP_API_KEY = "1c78cf22e8d628f3e830f6132bacb70f519fa7d5391a5d9666d21a687974f195"

INDIAN_STATES = [
    "All India", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir"
]

# -------------------------------------
# Location Detection
# -------------------------------------
def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()
        return data.get("region", "All India")
    except:
        return "All India"

# -------------------------------------
# Search with SerpAPI
# -------------------------------------
def fetch_urls(query, state_filter):
    from serpapi import GoogleSearch
    query_with_location = f"{query} in {state_filter}" if state_filter and state_filter != "All India" else query

    search = GoogleSearch({
        "q": query_with_location,
        "engine": "google",
        "api_key": SERP_API_KEY,
        "num": 20
    })

    results = search.get_dict()
    links = []

    for result in results.get("organic_results", []):
        link = result.get("link")
        if link and not link.startswith("https://webcache.googleusercontent.com"):
            links.append(link)

    return list(set(links))

# -------------------------------------
# Scraper
# -------------------------------------
def scrape_leads(urls, filters):
    leads = []

    for url in urls:
        try:
            response = requests.get(url, timeout=7)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()

            emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
            phones = re.findall(r"\b[7896]\d{9}\b", text)

            # Apply filters
            if filters == "Email Only" and not emails:
                continue
            if filters == "Phone Only" and not phones:
                continue
            if filters == "Email + Phone" and (not emails or not phones):
                continue

            leads.append({
                "Website": url,
                "Emails": ", ".join(set(emails)),
                "Phones": ", ".join(set(phones))
            })

        except Exception as e:
            continue

    return leads

# -------------------------------------
# Streamlit UI
# -------------------------------------
def main():
    st.set_page_config(page_title="Lead Scraper", layout="centered")
    st.title("🔍 Lead Scraper Tool (Free Beta)")

    user_state = get_user_location()
    with st.form("input_form"):
        keyword = st.text_input("Search Keyword", placeholder="e.g. Digital Marketing Agencies")
        col1, col2 = st.columns(2)
        with col1:
            state_filter = st.selectbox("📍 Location Filter (India)", INDIAN_STATES, index=INDIAN_STATES.index(user_state) if user_state in INDIAN_STATES else 0)
        with col2:
            data_filter = st.selectbox("🎯 Lead Type Filter", ["All", "Email Only", "Phone Only", "Email + Phone"])
        submit = st.form_submit_button("Scrape Leads")

    if submit:
        if not keyword.strip():
            st.error("Please enter a keyword.")
            return

        st.info("Fetching websites via SerpAPI...")
        urls = fetch_urls(keyword, state_filter)

        if not urls:
            st.error("No websites found.")
            return

        st.success(f"Found {len(urls)} websites. Scraping...")

        leads = scrape_leads(urls, data_filter)

        if not leads:
            st.warning("No leads found.")
        else:
            df = pd.DataFrame(leads)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"leads_{timestamp}.csv"

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            df.to_csv(tmp.name, index=False)
            tmp.close()

            st.success("✅ Done! Download your leads below:")
            st.download_button("📥 Download CSV", data=open(tmp.name, "rb"), file_name=filename, mime="text/csv")

if __name__ == "__main__":
    main()
