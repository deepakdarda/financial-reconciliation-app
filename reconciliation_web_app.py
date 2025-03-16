import streamlit as st
import pandas as pd
import os
from datetime import timedelta

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

def valuation_model(financial_df):
    # Placeholder for DCF and EBITDA-based valuation
    return financial_df  # To be expanded with actual valuation logic

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
    st.write("Upload **past 3-5 years of financials** to perform a valuation using **DCF and EBITDA-based methods**.")
    
    financial_file = st.file_uploader("Upload Financial Statements (CSV)", type=["csv"])
    
    if financial_file:
        financial_df = pd.read_csv(financial_file)
        
        st.write("### Preview of Financial Data")
        st.dataframe(financial_df.head())
        
        valuation_df = valuation_model(financial_df)
        
        st.write("### Valuation Results (To Be Implemented)")
        st.dataframe(valuation_df)
        
        csv = valuation_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Valuation Report", data=csv, file_name="Valuation_Report.csv", mime="text/csv")
