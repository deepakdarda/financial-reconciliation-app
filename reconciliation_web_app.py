import streamlit as st
import pandas as pd
import os
from datetime import timedelta

# Define Password Protection
PASSWORD = "India321"  # Change this to your preferred password

password = st.text_input("Enter Password:", type="password")

if password != PASSWORD:
    st.warning("Incorrect password. Please try again.")
    st.stop()
    
# Function to reconcile bank and ledger data
def reconcile_data(bank_df, ledger_df):
    bank_df["Date"] = pd.to_datetime(bank_df["Date"])
    ledger_df["Date"] = pd.to_datetime(ledger_df["Date"])
    
    # Merge exact matches
    merged_df = bank_df.merge(ledger_df, how="outer", on=["Date", "Amount"], suffixes=("_bank", "_ledger"))
    merged_df["Match Type"] = "Exact Match"
    
    # Identify bank-only and ledger-only entries
    merged_df.loc[merged_df["Description"].isna(), "Match Type"] = "Ledger Only (Not in Bank)"
    merged_df.loc[merged_df["Customer/Vendor Name"].isna(), "Match Type"] = "Bank Only (Not in Ledger)"
    
    # Handle date mismatches within ±5 days window
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

# Streamlit UI
st.title("Financial Reconciliation Tool")

st.write("Upload your **Bank Statement** and **Accounting Ledger** to perform reconciliation.")

# File uploaders
bank_file = st.file_uploader("Upload Bank Statement (CSV)", type=["csv"])
ledger_file = st.file_uploader("Upload Accounting Ledger (CSV)", type=["csv"])

if bank_file and ledger_file:
    # Load data
    bank_df = pd.read_csv(bank_file)
    ledger_df = pd.read_csv(ledger_file)
    
    st.write("### Preview of Uploaded Data")
    st.write("**Bank Statement:**")
    st.dataframe(bank_df.head())
    
    st.write("**Accounting Ledger:**")
    st.dataframe(ledger_df.head())
    
    # Run reconciliation
    reconciled_df = reconcile_data(bank_df, ledger_df)
    
    # Display results
    st.write("### Reconciliation Report")
    st.dataframe(reconciled_df)
    
    # Provide download link
    csv = reconciled_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Reconciliation Report", data=csv, file_name="Reconciliation_Report.csv", mime="text/csv")
