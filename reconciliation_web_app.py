import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import timedelta

# Function to calculate Build-Up Discount Rate for Private Firms
def build_up_discount_rate(risk_free_rate=0.03, industry_risk=0.06, size_premium=0.07, company_risk=0.10):
    return risk_free_rate + industry_risk + size_premium + company_risk

# Function to perform Discounted Cash Flow (DCF) valuation
def dcf_valuation(cash_flows, discount_rate, terminal_growth, years):
    terminal_value = cash_flows[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    discounted_cf = [cf / (1 + discount_rate) ** (i + 1) for i, cf in enumerate(cash_flows)]
    dcf_value = sum(discounted_cf) + (terminal_value / (1 + discount_rate) ** years)
    return dcf_value

# Function to perform EBITDA-based valuation
def ebitda_valuation(ebitda_list, multiple):
    weighted_ebitda = sum(ebitda * weight for ebitda, weight in zip(ebitda_list, [0.2, 0.3, 0.5]))
    return weighted_ebitda * multiple

# Function to calculate Book Value valuation
def book_valuation(total_assets, total_liabilities):
    return total_assets - total_liabilities

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
    st.write("Upload **past 3-5 years of financials** to perform a valuation using **DCF, EBITDA, and Book Value methods**.")
    
    financial_file = st.file_uploader("Upload Financial Statements (CSV)", type=["csv"])
    
    if financial_file:
        financial_df = pd.read_csv(financial_file)
        
        st.write("### Preview of Financial Data")
        st.dataframe(financial_df.head())
        
        discount_rate = build_up_discount_rate()
        terminal_growth = st.number_input("Enter Terminal Growth Rate (%)", min_value=0.0, max_value=0.1, value=0.02)
        ebitda_multiple = st.number_input("Enter Industry EBITDA Multiple", min_value=1.0, max_value=20.0, value=5.0)
        
        st.write(f"### Estimated Discount Rate (WACC for Private Firms): {discount_rate:.2%}")
        
        # Calculate DCF Valuation
        if "Cash Flow" in financial_df.columns:
            cash_flows = financial_df["Cash Flow"].dropna().tolist()
            dcf_value = dcf_valuation(cash_flows, discount_rate, terminal_growth, len(cash_flows))
            st.write(f"### DCF Valuation: ${dcf_value:,.2f}")
        
        # Calculate EBITDA Valuation
        if "EBITDA" in financial_df.columns:
            ebitda_list = financial_df["EBITDA"].dropna().tolist()[-3:]
            ebitda_value = ebitda_valuation(ebitda_list, ebitda_multiple)
            st.write(f"### EBITDA-Based Valuation: ${ebitda_value:,.2f}")
        
        # Calculate Book Value Valuation
        if "Total Assets" in financial_df.columns and "Total Liabilities" in financial_df.columns:
            book_value = book_valuation(financial_df["Total Assets"].iloc[-1], financial_df["Total Liabilities"].iloc[-1])
            st.write(f"### Book Value-Based Valuation: ${book_value:,.2f}")
        
        csv = financial_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Valuation Report", data=csv, file_name="Valuation_Report.csv", mime="text/csv")
