import streamlit as st
import pandas as pd
import os
import numpy as np
import requests
from datetime import timedelta

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

# Function to calculate WACC
def calculate_wacc(equity_value, debt_value, cost_of_equity, cost_of_debt, tax_rate):
    total_value = equity_value + debt_value
    wacc = (equity_value / total_value) * cost_of_equity + (debt_value / total_value) * cost_of_debt * (1 - tax_rate)
    return wacc

# Function to reconcile bank and ledger data
def reconcile_data(bank_df, ledger_df):
    bank_df["Date"] = pd.to_datetime(bank_df["Date"])
    ledger_df["Date"] = pd.to_datetime(ledger_df["Date"])
    
    merged_df = bank_df.merge(ledger_df, how="outer", on=["Date", "Amount"], suffixes=("_bank", "_ledger"))
    merged_df["Match Type"] = "Exact Match"
    
    merged_df.loc[merged_df["Description"].isna(), "Match Type"] = "Ledger Only (Not in Bank)"
    merged_df.loc[merged_df["Customer/Vendor Name"].isna(), "Match Type"] = "Bank Only (Not in Ledger)"
    
    for index, row in merged_df.iterrows():
        if row["Match Type"] != "Exact Match":
            potential_matches = ledger_df.loc[
                (ledger_df["Amount"] == row["Amount"]) & 
                (ledger_df["Date"] >= row["Date"] - timedelta(days=5)) & 
                (ledger_df["Date"] <= row["Date"] + timedelta(days=5))
            ]
            
            if not potential_matches.empty:
                merged_df.at[index, "Match Type"] = "Date Mismatch (±5 Days)"
                merged_df.at[index, "Customer/Vendor Name"] = potential_matches.iloc[0]["Customer/Vendor Name"]
    
    return merged_df

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
    st.title("Financial Reconciliation Tool")
    st.write("Upload your **Bank Statement** and **Accounting Ledger** to perform reconciliation.")
    
    bank_file = st.file_uploader("Upload Bank Statement (CSV)", type=["csv"])
    ledger_file = st.file_uploader("Upload Accounting Ledger (CSV)", type=["csv"])
    
    if bank_file and ledger_file:
        bank_df = pd.read_csv(bank_file)
        ledger_df = pd.read_csv(ledger_file)
        
        st.write("### Preview of Uploaded Data")
        st.write("**Bank Statement:**")
        st.dataframe(bank_df.head())
        
        st.write("**Accounting Ledger:**")
        st.dataframe(ledger_df.head())
        
        reconciled_df = reconcile_data(bank_df, ledger_df)
        
        st.write("### Reconciliation Report")
        st.dataframe(reconciled_df)
        
        csv = reconciled_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Reconciliation Report", data=csv, file_name="Reconciliation_Report.csv", mime="text/csv")

elif menu == "Valuation Model":
    st.title("Business Valuation Tool")
    st.write("Upload **a single Excel file with three financial statements (P&L, Cash Flow, Balance Sheet)** to perform valuation using **DCF, EBITDA, and Book Value methods**.")
    
    industry = st.text_input("Enter Industry Name (as per Damodaran's dataset)")
    
    uploaded_file = st.file_uploader("Upload Financial Statements (Excel, .xlsx)", type=["xlsx"])
    
    if uploaded_file:
        # Read Excel file with multiple sheets
        financial_data = pd.read_excel(uploaded_file, sheet_name=None)
        
        st.write("### Preview of Uploaded Data")
        for sheet_name, df in financial_data.items():
            st.write(f"**{sheet_name}**")
            st.dataframe(df.head())
        
        discount_rate = build_up_discount_rate(industry=industry)
        
        st.write(f"### Estimated Discount Rate (WACC for {industry}): {discount_rate:.2%}")
