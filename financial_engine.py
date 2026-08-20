"""
FINANCIAL STATEMENT ANALYSIS ENGINE (FMP API version)
Search any company -> auto-generates live financial statement reports.
Uses Financial Modeling Prep (FMP) as the data source (avoids Yahoo Finance rate limiting).
"""

import pandas as pd
import requests
import streamlit as st

FMP_BASE = "https://financialmodelingprep.com/stable"


def get_fmp_key():
    try:
        return st.secrets["FMP_API_KEY"]
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def resolve_ticker_fmp(company_query, api_key):
    url = f"{FMP_BASE}/search-name"
    params = {"query": company_query, "limit": 5, "apikey": api_key}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    results = r.json()
    if results:
        pick = results[0]
        return pick.get("symbol", company_query.upper()), pick.get("name", company_query)
    return company_query.upper(), company_query


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_statement_fmp(symbol, statement, period, api_key):
    endpoint_map = {
        "income": "income-statement",
        "balance": "balance-sheet-statement",
        "cashflow": "cash-flow-statement",
    }
    url = f"{FMP_BASE}/{endpoint_map[statement]}"
    params = {"symbol": symbol, "period": period, "limit": 5, "apikey": api_key}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def fmt(x):
    if x is None or pd.isna(x):
        return "N/A"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "N/A"
    if abs(x) >= 1e9:
        return f"${x/1e9:,.2f}B"
    if abs(x) >= 1e6:
        return f"${x/1e6:,.2f}M"
    return f"${x:,.0f}"


def pct_change_fmp(df, col):
    if df is None or df.empty or col not in df.columns or len(df) < 2:
        return None
    vals = df[col].dropna().tolist()
    if len(vals) < 2 or vals[1] == 0:
        return None
    return (vals[0] - vals[1]) / abs(vals[1]) * 100


def val(df, col, row=0):
    if df is None or df.empty or col not in df.columns:
        return None
    try:
        return df[col].iloc[row]
    except Exception:
        return None


class FinancialAnalysisEngineFMP:
    def __init__(self, company_query, period="annual"):
        self.query = company_query
        self.api_key = get_fmp_key()
        if not self.api_key:
            raise RuntimeError(
                "FMP_API_KEY not found in Streamlit secrets. "
                "Add it under Settings -> Secrets as FMP_API_KEY = \"your_key\"."
            )
        self.ticker, self.name = resolve_ticker_fmp(company_query, self.api_key)
        self.period = period
        self.inc = fetch_statement_fmp(self.ticker, "income", period, self.api_key)
        self.bs = fetch_statement_fmp(self.ticker, "balance", period, self.api_key)
        self.cf = fetch_statement_fmp(self.ticker, "cashflow", period, self.api_key)

    def dashboard_design(self):
        lines = [f"# Financial Statement Analysis: {self.name} ({self.ticker})\n"]

        lines.append("## Income Statement")
        rev = val(self.inc, "revenue")
        pc = pct_change_fmp(self.inc, "revenue")
        pc_str = f" (YoY change: {pc:.1f}%)" if pc is not None else ""
        lines.append(f"- Revenue: {fmt(rev)}{pc_str}")
        lines.append(f"- Cost of Revenue: {fmt(val(self.inc, 'costOfRevenue'))}")
        lines.append(f"- Gross Profit: {fmt(val(self.inc, 'grossProfit'))}")
        lines.append(f"- Operating Expenses: {fmt(val(self.inc, 'operatingExpenses'))}")
        lines.append(f"- Operating Income: {fmt(val(self.inc, 'operatingIncome'))}")
        lines.append(f"- Income Tax Expense: {fmt(val(self.inc, 'incomeTaxExpense'))}")
        lines.append(f"- Net Income: {fmt(val(self.inc, 'netIncome'))}\n")

        lines.append("## Balance Sheet")
        lines.append(f"- Cash & Equivalents: {fmt(val(self.bs, 'cashAndCashEquivalents'))}")
        lines.append(f"- Receivables: {fmt(val(self.bs, 'netReceivables'))}")
        lines.append(f"- Inventory: {fmt(val(self.bs, 'inventory'))}")
        lines.append(f"- Total Assets: {fmt(val(self.bs, 'totalAssets'))}")
        lines.append(f"- Total Debt: {fmt(val(self.bs, 'totalDebt'))}")
        lines.append(f"- Total Liabilities: {fmt(val(self.bs, 'totalLiabilities'))}")
        lines.append(f"- Shareholders Equity: {fmt(val(self.bs, 'totalStockholdersEquity'))}")
        lines.append(f"- Retained Earnings: {fmt(val(self.bs, 'retainedEarnings'))}\n")

        lines.append("## Cash Flow Statement")
        lines.append(f"- Operating Cash Flow: {fmt(val(self.cf, 'operatingCashFlow'))}")
        lines.append(f"- Investing Cash Flow: {fmt(val(self.cf, 'netCashProvidedByInvestingActivities'))}")
        lines.append(f"- Capital Expenditures: {fmt(val(self.cf, 'capitalExpenditure'))}")
        lines.append(f"- Financing Cash Flow: {fmt(val(self.cf, 'netCashProvidedByFinancingActivities'))}")
        lines.append(f"- Share Buybacks: {fmt(val(self.cf, 'commonStockRepurchased'))}")
        lines.append(f"- Dividends Paid: {fmt(val(self.cf, 'netDividendsPaid'))}")
        lines.append(f"- Net Change in Cash: {fmt(val(self.cf, 'netChangeInCash'))}\n")

        return "\n".join(lines)

    def cash_vs_profit(self):
        ni = val(self.inc, "netIncome")
        ocf = val(self.cf, "operatingCashFlow")
        lines = [f"# Cash vs Profit Investigation: {self.name} ({self.ticker})\n"]
        if ni is not None and ocf is not None:
            gap = ocf - ni
            verdict = "cash-generative (OCF exceeds net income)" if gap > 0 else "cash-hungry (OCF trails net income)"
            lines.append(f"- Net Income: {fmt(ni)}")
            lines.append(f"- Operating Cash Flow: {fmt(ocf)}")
            lines.append(f"- Gap (OCF - NI): {fmt(gap)} -> {verdict}")
        lines.append(f"- D&A: {fmt(val(self.cf, 'depreciationAndAmortization'))}")
        lines.append(f"- Stock-Based Comp: {fmt(val(self.cf, 'stockBasedCompensation'))}")
        lines.append(f"- Capex: {fmt(val(self.cf, 'capitalExpenditure'))}")
        return "\n".join(lines)

    def capital_allocation(self):
        lines = [f"# Capital Allocation Report: {self.name} ({self.ticker})\n"]
        lines.append(f"- R&D Spend: {fmt(val(self.inc, 'researchAndDevelopmentExpenses'))}")
        lines.append(f"- Capex: {fmt(val(self.cf, 'capitalExpenditure'))}")
        lines.append(f"- Share Buybacks: {fmt(val(self.cf, 'commonStockRepurchased'))}")
        lines.append(f"- Dividends Paid: {fmt(val(self.cf, 'netDividendsPaid'))}")
        lines.append(f"- Debt Repayment: {fmt(val(self.cf, 'debtRepayment'))}")
        return "\n".join(lines)

    def storytelling(self):
        d = self.dashboard_design()
        return d.replace("Financial Statement Analysis", "Financial Storytelling Report")


def run_search(company_query, report_type="dashboard", period="annual"):
    engine = FinancialAnalysisEngineFMP(company_query, period=period)
    if report_type == "dashboard":
        return engine.dashboard_design()
    elif report_type == "storytelling":
        return engine.storytelling()
    elif report_type == "cash_vs_profit":
        return engine.cash_vs_profit()
    elif report_type == "capital_allocation":
        return engine.capital_allocation()
