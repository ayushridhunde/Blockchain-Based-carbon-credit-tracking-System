import streamlit as st
from web3 import Web3
import os
import json
import pandas as pd
from dotenv import load_dotenv
import datetime # Import ko upar rakhein

# 1. Load environment variables
load_dotenv()
contract_address = os.getenv("CONTRACT_ADDRESS")
infura_url = os.getenv("INFURA_URL")
sender_address = os.getenv("SENDER_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")

# 2. Setup ABI and Web3 connection
with open("abi.json") as f:
    contract_abi = json.load(f)

w3 = Web3(Web3.HTTPProvider(infura_url))
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# 3. Initialize Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN PAGE ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>🔐 Carbon Tracker Login</h1>", unsafe_allow_html=True)
    with st.container():
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- MAIN DASHBOARD ---
def main_dashboard():
    st.sidebar.title("Settings")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if w3.is_connected():
        st.sidebar.success("Connected to Sepolia")
    else:
        st.sidebar.error("Connection Failed")

    st.title("🌱 Blockchain Carbon Credit Tracker")
    tab1, tab2 = st.tabs(["➕ Add Credits", "📜 View History"])

    with tab1:
        st.header("Register New Carbon Credit")
        company = st.text_input("Company Name", placeholder="e.g. Tata Industries")
        amount = st.number_input("Credit Amount (Tons)", min_value=1)
        
        if st.button("Submit to Blockchain"):
            import streamlit as st
            if st.button("Register Carbon Credit"):
                if company_name and amount > 0:
        try:
            with st.spinner("Broadcasting transaction to Ethereum Sepolia..."):
                # 1. Trigger the Smart Contract function
                # This returns the raw Transaction Hash (HexBytes)
                tx_hash = contract.functions.addCredit(company_name, int(amount)).transact()

                # 2. Wait for the block to be mined (Optional, but looks professional)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                # 3. Success Message
                st.success("Transaction Successful!")
                st.balloons() # Visual effect for the presentation

                # 4. Display the Hash ID directly on the screen
                # Use .hex() to convert the raw bytes into a readable string
                hash_id = tx_hash.hex()
                
                st.subheader("Blockchain Receipt")
                st.info(f"**Transaction Hash ID:**")
                st.code(hash_id) # This adds a 'copy' button automatically

                # 5. Create a direct hyperlink to Etherscan for the examiner
                etherscan_link = f"https://sepolia.etherscan.io/tx/{hash_id}"
                st.markdown(f"🔗 [View Live on Sepolia Etherscan]({etherscan_link})")

        except Exception as e:
            st.error(f"Transaction Failed: {e}")
    else:
        st.warning("Please enter valid company details and credit amount.")
            if company:
                try:
                    with st.spinner("Processing transaction..."):
                        nonce = w3.eth.get_transaction_count(sender_address)
                        tx = contract.functions.addCredit(company, amount).build_transaction({
                            'chainId': 11155111,
                            'gas': 200000,
                            'gasPrice': w3.eth.gas_price,
                            'nonce': nonce,
                        })
                        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction) 
                        st.success(f"Transaction Sent! Hash: {w3.to_hex(tx_hash)}")
                except Exception as e:
                    st.error(f"Blockchain Error: {e}")
            else:
                st.warning("Please enter a company name.")

    with tab2:
        st.header("Carbon Credit Ledger")
        if st.button("Fetch Latest Data"):
            try:
                data = contract.functions.getCredits().call()
                if data:
                    df = pd.DataFrame(data, columns=["Company Name", "Credits (Tons)", "Timestamp"])
                    # FIXED: Formatting yahan honi chahiye
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s').dt.strftime('%d-%m-%Y %H:%M')
                    st.table(df)
                else:
                    st.info("No records found on the blockchain.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# --- APP FLOW CONTROL ---
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()
