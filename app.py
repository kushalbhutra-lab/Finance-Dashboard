import streamlit as st
from financial_engine import run_search

st.set_page_config(page_title="Live Financial Statement Analyzer", layout="wide")

st.title("Live Financial Statement Analysis Engine")
st.caption("Search any listed company. Data is pulled live via the Financial Modeling Prep API.")

if "FMP_API_KEY" not in st.secrets:
    st.error(
        "No FMP_API_KEY found in Streamlit secrets. "
        "Go to your app settings -> Secrets, and add:\n\n"
        "FMP_API_KEY = \"your_api_key_here\"\n\n"
        "Get a free key at financialmodelingprep.com/developer/docs"
    )
    st.stop()

col1, col2, col3 = st.columns([3, 2, 1.5])
with col1:
    company_query = st.text_input("Enter company name or ticker", value="NVIDIA", placeholder="e.g. Apple, Tesla, MSFT")
with col2:
    report_type = st.selectbox(
        "Select report type",
        options=[
            ("dashboard", "1. Dashboard Design (Full Statement Breakdown)"),
            ("storytelling", "2. Financial Storytelling Analyst"),
            ("cash_vs_profit", "3. Cash vs Profit Investigation"),
            ("capital_allocation", "4. Capital Allocation and Financial Strategy"),
        ],
        format_func=lambda x: x[1],
    )
with col3:
    period = st.selectbox("Period", options=["annual", "quarter"])

run_btn = st.button("Run Analysis", type="primary")

if run_btn:
    if not company_query.strip():
        st.warning("Please enter a company name or ticker.")
    else:
        with st.spinner(f"Fetching live financial statements for {company_query}..."):
            try:
                report_text = run_search(company_query, report_type[0], period)
                st.success("Report generated from live data.")
                st.markdown(report_text)
                st.download_button(
                    label="Download report as .md",
                    data=report_text,
                    file_name=f"{company_query.replace(chr(32), chr(95))}_{report_type[0]}_report.md",
                    mime="text/markdown",
                )
            except Exception as e:
                st.error(f"Could not fetch data for '{company_query}'. Error: {e}")
                st.info("Try using the exact stock ticker (e.g. AAPL, NVDA, TSLA) if the company name search fails.")

st.divider()
st.caption("Data source: Financial Modeling Prep API. Figures reflect the most recently reported filing.")
