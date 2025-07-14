import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import tempfile
from datetime import datetime
from serpapi import GoogleSearch

# 🌍 Indian States for Manual Selection
INDIAN_STATES = [
    "All India", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir"
]

# 🌍 Detect user's state using IP
def detect_user_state():
    try:
        ip_info = requests.get("https://ipinfo.io/json").json()
        region = ip_info.get("region", "")
        return region if region in INDIAN_STATES else "All India"
    except:
        return "All India"

# 🔎 Fetch website URLs using SerpAPI
def fetch_urls(query, state):
    SERP_API_KEY = st.secrets["SERP_API_KEY"]
    full_query = f"{query} in {state}" if state != "All India" else query

    params = {
        "engine": "google",
        "q": full_query,
        "api_key": SERP_API_KEY,
        "num": 10
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    links = []

    if "organic_results" in results:
        for result in results["organic_results"]:
            link = result.get("link")
            if link:
                links.append(link)

    return links

# 🕵️‍♀️ Scrape emails & phone numbers
def scrape_leads(urls):
    leads = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()

            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            phones = re.findall(r"\b\d{10}\b", text)

            unique_emails = list(set(emails))
            unique_phones = list(set(phones))

            leads.append({
                "Website": url,
                "Emails": ", ".join(unique_emails),
                "Phones": ", ".join(unique_phones)
            })
        except:
            continue

    return leads

# 🚀 Streamlit UI
def main():
    st.set_page_config(page_title="Lead Scraper", layout="centered")
    st.title("🔍 Lead Scraper Tool (Free Beta)")

    detected_state = detect_user_state()
    st.write(f"📍 Auto-detected Location: `{detected_state}`")

    state_filter = st.selectbox("🎯 Select your state (or override)", INDIAN_STATES,
                                index=INDIAN_STATES.index(detected_state))

    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("Enter your search keyword:", placeholder="e.g., sports shop")
    with col2:
        filter_option = st.selectbox("Filter leads with:", ["All", "Email only", "Phone only", "Both"])

    if st.button("Scrape Leads"):
        if not keyword.strip():
            st.error("Please enter a keyword.")
            return

        st.info("🔎 Fetching websites...")
        urls = fetch_urls(keyword, state_filter)

        if not urls:
            st.error("No valid websites found.")
            return

        st.success(f"🌐 Found {len(urls)} websites. Scraping now...")

        leads = scrape_leads(urls)

        if not leads:
            st.warning("No leads found. Try different keywords.")
            return

        df = pd.DataFrame(leads)

        # Apply filters
        if filter_option == "Email only":
            df = df[df["Emails"].str.strip() != ""]
            df = df[df["Phones"].str.strip() == ""]
        elif filter_option == "Phone only":
            df = df[df["Phones"].str.strip() != ""]
            df = df[df["Emails"].str.strip() == ""]
        elif filter_option == "Both":
            df = df[(df["Emails"].str.strip() != "") & (df["Phones"].str.strip() != "")]

        if df.empty:
            st.warning("No leads matched the selected filter.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_{timestamp}.csv"

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.to_csv(tmp.name, index=False)
        tmp.close()

        st.success("✅ Done! Download your leads file below:")
        st.download_button("📥 Download CSV", data=open(tmp.name, "rb"), file_name=filename, mime="text/csv")

if __name__ == "__main__":
    main()
