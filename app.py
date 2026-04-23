import streamlit as st
import pandas as pd
from apollo_scraper import search_apollo_leads, format_lead_data, export_to_csv, export_to_google_sheets

st.set_page_config(page_title="Apollo Lead Scraper", page_icon="🚀", layout="wide")

st.title("🚀 Apollo B2B Lead Scraper Dashboard")
st.markdown("Visually extract leads based on your specific parameters and export them locally or directly to Google Sheets.")

with st.sidebar:
    st.header("Search Filters")
    
    # Domains (optional)
    st.markdown("**Company Domains (Optional)**")
    domains_input = st.text_area("Target Domains (comma-separated)", placeholder="e.g., amazon.com")
    
    # Job Titles
    st.markdown("**Job Titles**")
    titles_input = st.text_area("Target Job Titles (comma-separated)", value="Marketing Manager")
    
    # Target Industries
    st.markdown("**Target Industries (Optional)**")
    industries_input = st.text_area("Industries (comma-separated)", placeholder="e.g., software, real estate, manufacturing")
    
    # Location
    st.markdown("**Location**")
    locations_input = st.text_input("Target Location (comma-separated)", value="Mumbai, India")
    
    # Employee Size
    st.markdown("**Company Employee Size**")
    size_50_100 = st.checkbox("51 - 100", value=True)
    size_100_500 = st.checkbox("101 - 500")
    size_500_plus = st.checkbox("500+")
    
    # Email Status
    st.markdown("**Email Status**")
    verified_only = st.checkbox("Verified Emails Only", value=True)
    
    # Limit
    st.markdown("**Fetch Limits**")
    limit = st.slider("Number of leads to fetch", min_value=1, max_value=100, value=10)

    run_btn = st.button("Run Scraper", type="primary", use_container_width=True)

if run_btn:
    # Process inputs
    domains = [d.strip() for d in domains_input.split(",") if d.strip()] if domains_input else None
    titles = [t.strip() for t in titles_input.split(",") if t.strip()] if titles_input else None
    locations = [l.strip() for l in locations_input.split(",") if l.strip()] if locations_input else None
    industries = [i.strip() for i in industries_input.split(",") if i.strip()] if industries_input else None
    
    emp_ranges = []
    if size_50_100: emp_ranges.append("51,100")
    if size_100_500: 
        emp_ranges.append("101,250")
        emp_ranges.append("251,500")
    if size_500_plus:
        emp_ranges.extend(["501,1000", "1001,5000", "5001,10000", "10001"])
        
    email_status = ["verified"] if verified_only else None

    with st.spinner("Fetching data from Apollo.io..."):
        result = search_apollo_leads(
            domains=domains,
            job_titles=titles,
            locations=locations,
            employee_ranges=emp_ranges,
            email_status=email_status,
            industries=industries,
            limit=limit
        )

    if "error" in result:
        st.error(result["error"])
    else:
        people = result["people"]
        if not people:
            st.warning("No leads found matching your criteria. Try broadening your search.")
        else:
            st.success(f"Successfully retrieved {len(people)} leads!")
            
            # Format and display
            formatted_leads = format_lead_data(people)
            df = pd.DataFrame(formatted_leads)
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            st.subheader("Export Options")
            # Action Buttons
            col1, col2 = st.columns(2)
            
            with col1:
                export_to_csv(formatted_leads)
                with open("leads_output.csv", "rb") as file:
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=file,
                        file_name="leads_output.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col2:
                with st.spinner("Exporting to Google Sheets..."):
                    gs_result = export_to_google_sheets(formatted_leads)
                    if gs_result == "Success":
                        st.success("✅ Appended to Google Sheets!")
                    else:
                        st.error(f"Google Sheets Error: {gs_result}")
