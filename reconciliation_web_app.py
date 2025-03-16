import streamlit as st
import pandas as pd
import os
import numpy as np
import requests
from datetime import timedelta

# Apply custom styles to improve UI
def set_custom_styles():
    st.markdown(
        """
        <style>
        /* Background and font styling */
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f8f9fa;
        }
        
        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #343a40 !important;
            color: white;
        }
        
        /* Title styling */
        h1, h2, h3 {
            color: #007bff;
        }
        
        /* Card styling for data display */
        .stDataFrame {
            border-radius: 10px;
            border: 1px solid #ddd;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #007bff;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to fetch industry risk premium from Damodaran's site
def fetch_industry_risk_premium(industry):
    try:
        url = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/indprc.xls"
        df = pd.read_excel(url, sheet_name=None)
        industry_data = df[list(df.keys())[0]]  # Extract first sheet
        industry_risk = industry_data[industry_data.iloc[:, 0].str.contains(industry, case=False, na=False)].iloc[:, -1].values
        return float(industry_risk[0]) if len(industry_risk) > 0 else 0.06  # Default 6% if not found
    except:
        return 0.06  # Default fallback value

# Function to calculate Build-Up Discount Rate for Private Firms
def build_up_discount_rate(risk_free_rate=0.03, industry="Other", size_premium=0.07, company_risk=0.10):
    industry_risk = fetch_industry_risk_premium(industry)
    return risk_free_rate + industry_risk + size_premium + company_risk

# Apply UI improvements
set_custom_styles()

# Password Protection
PASSWORD = "securepass"
password = st.text_input("Enter Password:", type="password")
if password != PASSWORD:
    st.warning("Incorrect password. Please try again.")
    st.stop()

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select Function:", ["Financial Reconciliation", "Valuation Model"])

if menu == "Financial Reconciliation":
    st.title("📊 Financial Reconciliation Tool")
    st.write("Upload your **Bank Statement** and **Accounting Ledger** to perform reconciliation.")
    
    bank_file = st.file_uploader("📂 Upload Bank Statement (CSV)", type=["csv"])
    ledger_file = st.file_uploader("📂 Upload Accounting Ledger (CSV)", type=["csv"])
    
    if bank_file and ledger_file:
        bank_df = pd.read_csv(bank_file)
        ledger_df = pd.read_csv(ledger_file)
        
        st.write("### 🔍 Preview of Uploaded Data")
        st.write("**📄 Bank Statement:**")
        st.dataframe(bank_df.head())
        
        st.write("**📄 Accounting Ledger:**")
        st.dataframe(ledger_df.head())
        
        reconciled_df = bank_df.merge(ledger_df, how="outer", on=["Date", "Amount"], suffixes=("_bank", "_ledger"))
        reconciled_df["Match Type"] = "Exact Match"
        reconciled_df.loc[reconciled_df["Description"].isna(), "Match Type"] = "Ledger Only (Not in Bank)"
        reconciled_df.loc[reconciled_df["Customer/Vendor Name"].isna(), "Match Type"] = "Bank Only (Not in Ledger)"
        
        st.write("### ✅ Reconciliation Report")
        st.dataframe(reconciled_df)
        
        csv = reconciled_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Reconciliation Report", data=csv, file_name="Reconciliation_Report.csv", mime="text/csv")

elif menu == "Valuation Model":
    st.title("💰 Business Valuation Tool")
    st.write("Upload **a single Excel file with three financial statements (P&L, Cash Flow, Balance Sheet)** to perform valuation using **DCF, EBITDA, and Book Value methods**.")
    
    industry = st.text_input("📌 Enter Industry Name (as per Damodaran's dataset)")
    
    uploaded_file = st.file_uploader("📂 Upload Financial Statements (Excel, .xlsx)", type=["xlsx"])
    
    if uploaded_file:
        # Read Excel file with multiple sheets
        financial_data = pd.read_excel(uploaded_file, sheet_name=None)
        
        st.write("### 📊 Preview of Uploaded Data")
        for sheet_name, df in financial_data.items():
            st.write(f"**📄 {sheet_name}**")
            st.dataframe(df.head())
        
        discount_rate = build_up_discount_rate(industry=industry)
        
        st.write(f"### 📈 Estimated Discount Rate (WACC for {industry}): {discount_rate:.2%}")
