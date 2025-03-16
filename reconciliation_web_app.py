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

# Password Protection
PASSWORD = "securepass"
password = st.text_input("Enter Password:", type="password")
if password != PASSWORD:
    st.warning("Incorrect password. Please try again.")
    st.stop()

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select Function:", ["Financial Reconciliation", "Valuation Model"])

if menu == "Valuation Model":
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
        terminal_growth = st.number_input("Enter Terminal Growth Rate (%)", min_value=0.0, max_value=0.1, value=0.02)
        ebitda_multiple = st.number_input("Enter Industry EBITDA Multiple", min_value=1.0, max_value=20.0, value=5.0)
        
        # Extract financials from uploaded data
        cash_flows = []
        ebitda_list = []
        total_assets = 0
        total_liabilities = 0
        equity_value = 0
        debt_value = 0
        interest_expense = 0
        tax_rate = 0.25  # Default tax rate
        
        if "Cash Flow" in financial_data:
            cash_flow_df = financial_data["Cash Flow"]
            if "Cash from Operations" in cash_flow_df.columns:
                cash_flows.append(cash_flow_df["Cash from Operations"].sum())
        
        if "Profit & Loss" in financial_data:
            pl_df = financial_data["Profit & Loss"]
            if "EBITDA" in pl_df.columns:
                ebitda_list.append(pl_df["EBITDA"].sum())
            if "Interest Expense" in pl_df.columns:
                interest_expense += pl_df["Interest Expense"].sum()
        
        if "Balance Sheet" in financial_data:
            bs_df = financial_data["Balance Sheet"]
            if "Total Assets" in bs_df.columns:
                total_assets = bs_df["Total Assets"].iloc[-1]
            if "Total Liabilities" in bs_df.columns:
                total_liabilities = bs_df["Total Liabilities"].iloc[-1]
            if "Equity" in bs_df.columns:
                equity_value = bs_df["Equity"].iloc[-1]
            if "Debt" in bs_df.columns:
                debt_value = bs_df["Debt"].iloc[-1]
        
        cost_of_equity = discount_rate
        cost_of_debt = interest_expense / debt_value if debt_value else 0.05
        wacc = calculate_wacc(equity_value, debt_value, cost_of_equity, cost_of_debt, tax_rate)
        
        st.write(f"### Estimated Discount Rate (WACC for {industry}): {wacc:.2%}")
        st.write(f"### Current Debt to Equity Ratio: {debt_value / equity_value if equity_value else 'N/A'}")
        
        # Calculate DCF Valuation
        if cash_flows:
            dcf_value = dcf_valuation(cash_flows, wacc, terminal_growth, len(cash_flows))
            st.write(f"### DCF Valuation: ${dcf_value:,.2f}")
        
        # Calculate EBITDA Valuation
        if ebitda_list:
            ebitda_value = ebitda_valuation(ebitda_list, ebitda_multiple)
            st.write(f"### EBITDA-Based Valuation: ${ebitda_value:,.2f}")
        
        # Calculate Book Value Valuation
        if total_assets and total_liabilities:
            book_value = book_valuation(total_assets, total_liabilities)
            st.write(f"### Book Value-Based Valuation: ${book_value:,.2f}")
