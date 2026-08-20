# Live Financial Statement Analysis Engine (FMP API version)

## Files in this repo
- app.py
- financial_engine.py
- requirements.txt
- .streamlit/secrets.toml.example  (rename to secrets.toml locally, never commit the real one)
- .gitignore

## Setup
1. Get a free FMP API key at https://site.financialmodelingprep.com/developer/docs
2. On Streamlit Community Cloud: App -> Settings -> Secrets -> add:
   FMP_API_KEY = "your_actual_key_here"
3. Push all files (except secrets.toml) to GitHub, then Reboot the app on Streamlit Cloud.

## Local run
pip install -r requirements.txt
# create .streamlit/secrets.toml locally with your key first
streamlit run app.py

## Report types
1. Dashboard Design - full line-by-line income statement, balance sheet, cash flow breakdown
2. Financial Storytelling Analyst - narrative version of the same data
3. Cash vs Profit Investigation - net income vs operating cash flow, earnings quality check
4. Capital Allocation and Financial Strategy - R&D, capex, buybacks, dividends, debt repayment
