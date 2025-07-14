import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import tempfile
from datetime import datetime
from serpapi import GoogleSearch  # ← ADD THIS

SERP_API_KEY = st.secrets["SERPAPI_KEY"]

INDIAN_STATES = [
    "All India", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir"
]

def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json")
        return res.json().get("region", "All India")
    except:
        return "All India"

def fetch_urls(query, state_filter):
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

def scrape_leads(urls, filters):
    leads = []

    for url in urls:
        try:
            response = requests.get(url, timeout=7)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()

            emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
            phones = re.findall(r"\b[7896]\d{9}\b", text)

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

        except:
            continue

    return leads
