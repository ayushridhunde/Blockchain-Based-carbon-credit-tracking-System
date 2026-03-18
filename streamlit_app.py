import streamlit as st
import streamlit_authenticator as stauth
import yaml
import pandas as pd
from yaml.loader import SafeLoader
from web3 import Web3
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Carbon Credit Blockchain", layout="wide")

# --- 2. BLOCKCHAIN CONNECTION SETUP ---
w3 = Web3(Web3.HTTPProvider(st.secrets["ALCHEMY_URL"]))
contract_address = w3.to_checksum_address("0x9BBfACd347eA9526B3CF9cE2F8A9c16DFC95777d")

# Complete ABI (Application Binary Interface)
abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "_company", "type": "string"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"}
        ],
        "name": "addCredit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getCredits",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "company", "type": "string"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
                ],
                "internalType": "struct CarbonCredit.Credit[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=abi)

# --- 3. AUTHENTICATION SETUP ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Render the Login Widget
authenticator.login(location='main')

# --- 4. DASHBOARD CONTENT (ONLY SHOWN IF LOGGED IN) ---
if st.session_state["authentication_status"]:
    # Sidebar: Logout & Wallet Info
    authenticator.logout('Logout', 'sidebar')
    
    st.sidebar.divider()
    st.sidebar.header("System Status")
    if w3.is_connected():
        st.sidebar.success("Blockchain: Connected")
        balance = w3.eth.get_balance(w3.eth.accounts[0])
        st.sidebar.metric("Admin Balance", f"{w3.from_wei(balance, 'ether'):.2f} ETH")
    else:
        st.sidebar.error("Blockchain: Disconnected")

    # Sidebar: Carbon Footprint Calculator
    st.sidebar.divider()
    st.sidebar.header("Footprint Calculator")
    emissions = st.sidebar.number_input("Enter CO2 Emissions (tons)", min_value=0)
    credits_needed = emissions * 1.5 
    st.sidebar.write(f"**Recommended Credits:** {credits_needed}")
    if st.sidebar.button("Use this Amount"):
        st.session_state['recommended_val'] = credits_needed

    # Main Dashboard Header
    st.title("🌱 Carbon Credit Blockchain Dashboard")
    st.write(f"Logged in as: **{st.session_state['name']}**")

    # --- SECTION: ADD NEW CREDIT ---
    st.divider()
    st.subheader("Add New Carbon Credit Transaction")
    with st.form("credit_form"):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", placeholder="e.g. Tata Industries")
        with col2:
            default_val = int(st.session_state.get('recommended_val', 1))
            credit_amount = st.number_input("Credit Amount (tons)", min_value=1, value=default_val)
        
        submit_button = st.form_submit_button("Record on Blockchain")

    if submit_button:
        try:
            account = w3.eth.accounts[0]
            tx_hash = contract.functions.addCredit(str(company_name), int(credit_amount)).transact({'from': account})
            w3.eth.wait_for_transaction_receipt(tx_hash)
            st.success(f"Transaction Successful! Hash: {tx_hash.hex()}")
            st.rerun() # Refresh to show new data in table/chart
        except Exception as e:
            st.error(f"Blockchain Error: {e}")

    # --- SECTION: ANALYTICS & HISTORY ---
    st.divider()
    try:
        history = contract.functions.getCredits().call()
        if history:
            # Prepare data for display
            formatted_data = []
            for item in history:
                formatted_data.append({
                    "Company": item[0],
                    "Credits": item[1],
                    "Timestamp": datetime.fromtimestamp(item[2]).strftime('%Y-%m-%d %H:%M')
                })
            
            df = pd.DataFrame(formatted_data)

            # Dashboard Columns for Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Credits Issued", f"{df['Credits'].sum()} tons")
            m2.metric("Total Transactions", len(df))
            m3.metric("Partner Companies", df['Company'].nunique())

            # Data Visualization
            st.subheader("Credit Distribution Analysis")
            chart_data = df.groupby("Company")["Credits"].sum()
            st.bar_chart(chart_data)

            # Transaction Table
            st.subheader("Immutable Transaction Ledger")
            st.dataframe(df, use_container_width=True)
            
            # Export Feature
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Blockchain Report", data=csv, file_name='carbon_report.csv', mime='text/csv')
            
        else:
            st.info("No credit transactions found on the blockchain ledger yet.")
    except Exception as e:
        st.error(f"Error fetching data from smart contract: {e}")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')

elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your credentials to access the blockchain.')
