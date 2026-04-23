import os
import requests
import pandas as pd
import gspread
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

def get_secret(key):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)

APOLLO_API_KEY = get_secret("APOLLO_API_KEY")
GOOGLE_SHEET_URL = get_secret("GOOGLE_SHEET_URL")
APOLLO_SEARCH_URL = "https://api.apollo.io/v1/mixed_people/search"

def search_apollo_leads(domains=None, job_titles=None, locations=None, employee_ranges=None, email_status=None, industries=None, limit=10):
    """
    Search Apollo.io for people based on various parameters.
    """
    if not APOLLO_API_KEY or APOLLO_API_KEY == "your_api_key_here":
        return {"error": "API Key is missing. Please set APOLLO_API_KEY in your .env file."}

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }

    payload = {
        "api_key": APOLLO_API_KEY,
        "page": 1,
        "per_page": limit,
    }
    
    if domains:
        payload["q_organization_domains"] = "\n".join(domains) if isinstance(domains, list) else domains
        
    if job_titles:
        payload["person_titles"] = job_titles
        
    if locations:
        payload["person_locations"] = locations
        
    if employee_ranges:
        payload["organization_num_employees_ranges"] = employee_ranges
        
    if email_status:
        payload["contact_email_status"] = email_status
        
    if industries:
        payload["organization_industry_tag_ids"] = industries

    try:
        response = requests.post(APOLLO_SEARCH_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return {"success": True, "people": data.get("people", [])}
        else:
            return {"error": f"API Error {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def format_lead_data(people_data):
    """
    Extract the required fields and return a list of dictionaries.
    """
    extracted_leads = []
    for person in people_data:
        org = person.get("organization") or {}
        lead = {
            "First Name": person.get("first_name", "N/A"),
            "Last Name": person.get("last_name", "N/A"),
            "Job Title": person.get("title", "N/A"),
            "Company Name": org.get("name", "N/A"),
            "Email": person.get("email", "N/A"),
            "Email Status": person.get("email_status", "N/A")
        }
        extracted_leads.append(lead)
    return extracted_leads

def export_to_csv(formatted_leads, output_file="leads_output.csv"):
    if not formatted_leads: return False
    df = pd.DataFrame(formatted_leads)
    df.to_csv(output_file, index=False)
    return True

def export_to_google_sheets(formatted_leads):
    if not formatted_leads: return "No data to export."
    if not GOOGLE_SHEET_URL or GOOGLE_SHEET_URL == "your_google_sheet_url_here":
        return "Google Sheet URL missing in .env"
        
    credentials_file = "credentials.json"
    if not os.path.exists(credentials_file):
        return "credentials.json not found."
        
    try:
        gc = gspread.service_account(filename=credentials_file)
        sheet = gc.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        headers = ["First Name", "Last Name", "Job Title", "Company Name", "Email", "Email Status"]
        if not sheet.get_all_values():
            sheet.append_row(headers)
            
        rows_to_append = [[lead["First Name"], lead["Last Name"], lead["Job Title"], lead["Company Name"], lead["Email"], lead["Email Status"]] for lead in formatted_leads]
        sheet.append_rows(rows_to_append)
        return "Success"
    except Exception as e:
        return str(e)
