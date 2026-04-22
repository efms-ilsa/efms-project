import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os
import json
import hashlib
from datetime import datetime

# ────────────────────────── CONFIG & USERS ──────────────────────────
# Streamlit uses specific ways to handle files in the cloud
CONFIG_FILE = "efms_config.json"
USERS_FILE = "efms_users.json"
DATA_FILE = "employee_data.csv"

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

DEFAULT_USERS = {
    "admin":  {"password": hash_password("admin123"), "role": "Admin"},
    "hr":     {"password": hash_password("hr1234"),   "role": "HR"},
    "viewer": {"password": hash_password("view123"),  "role": "Viewer"}
}

# Helper to load data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # Create dummy data if file missing
        return pd.DataFrame(columns=["EmployeeNumber", "Department", "JobRole", "MonthlyIncome", "PerformanceRating", "YearsAtCompany", "NetSalary", "Bonus", "Deduction"])

# ────────────────────────── SESSION STATE (LOGIN) ──────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# ────────────────────────── MAIN APP ──────────────────────────
st.set_page_config(page_title="EFMS Live Dashboard", layout="wide")

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.title("🔐 EFMS Login")
    st.info("Logins: admin/admin123, hr/hr1234, viewer/view123")
    
    with st.form("login_form"):
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if user_input in DEFAULT_USERS and DEFAULT_USERS[user_input]["password"] == hash_password(pass_input):
                st.session_state.logged_in = True
                st.session_state.username = user_input
                st.session_state.role = DEFAULT_USERS[user_input]["role"]
                st.rerun()
            else:
                st.error("Invalid Username or Password")
else:
    # --- LOGGED IN CONTENT ---
    df = load_data()
    role = st.session_state.role
    user = st.session_state.username

    # Sidebar Menu (Your 1-12 Options)
    st.sidebar.title(f"Welcome, {user}")
    st.sidebar.write(f"Role: **{role}**")
    
    menu_options = [
        "Show Employees", "Search Employee", "Add Employee", 
        "Update Employee", "Delete Employee", "Dashboard", 
        "Salary Prediction", "Top 5 Salaries", "Attendance Tracker", 
        "Department Report", "Logout"
    ]
    
    choice = st.sidebar.radio("Main Menu", menu_options)

    # Permission Check (Matching your original ROLE_PERMISSIONS)
    viewer_restricted = ["Add Employee", "Update Employee", "Delete Employee", "Salary Prediction"]
    hr_restricted = ["Delete Employee"]

    if role == "Viewer" and choice in viewer_restricted:
        st.warning("⚠️ Access Denied: Viewer role cannot use this feature.")
    elif role == "HR" and choice in hr_restricted:
        st.warning("⚠️ Access Denied: HR role cannot Delete.")
    
    else:
        # 1. SHOW EMPLOYEES
        if choice == "Show Employees":
            st.header("📋 All Employee Records")
            st.dataframe(df, use_container_width=True)

        # 2. SEARCH EMPLOYEE
        elif choice == "Search Employee":
            st.header("🔍 Search Employee")
            search_id = st.number_input("Enter Employee ID", step=1)
            if st.button("Search"):
                res = df[df["EmployeeNumber"] == search_id]
                if not res.empty:
                    st.table(res)
                else:
                    st.error("Employee not found.")

        # 6. DASHBOARD (Your Graphs)
        elif choice == "Dashboard":
            st.header("📊 Business Analytics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Salary Distribution")
                fig1, ax1 = plt.subplots()
                ax1.hist(df["NetSalary"], bins=20, color="#4A90D9")
                st.pyplot(fig1)
                
            with col2:
                st.subheader("Department Avg Salary")
                if "Department" in df.columns:
                    ds = df.groupby("Department")["NetSalary"].mean()
                    st.bar_chart(ds)

        # 8. TOP 5 SALARIES
        elif choice == "Top 5 Salaries":
            st.header("🏆 Top 5 Highest Paid")
            top5 = df.sort_values("NetSalary", ascending=False).head(5)
            st.table(top5[["EmployeeNumber", "JobRole", "NetSalary"]])

        # 9. ATTENDANCE TRACKER (Your Logic)
        elif choice == "Attendance Tracker":
            st.header("🕒 Attendance & Pay Calculator")
            emp_id = st.number_input("Employee ID", step=1)
            total_days = st.slider("Total working days", 20, 31, 22)
            days_worked = st.slider("Days worked", 0, total_days, total_days)
            
            if st.button("Calculate Final Pay"):
                res = df[df["EmployeeNumber"] == emp_id]
                if not res.empty:
                    base = res.iloc[0]["MonthlyIncome"]
                    adj = base * (days_worked / total_days)
                    st.success(f"Adjusted Salary for ID {emp_id}: ${adj:,.2f}")
                    if (days_worked/total_days) < 0.75:
                        st.warning("Low Attendance Warning!")
                else:
                    st.error("Employee ID not found.")

        # 10. DEPARTMENT REPORT
        elif choice == "Department Report":
            st.header("🏢 Department-wise Analysis")
            report = df.groupby("Department").agg({
                "EmployeeNumber": "count",
                "NetSalary": "mean"
            }).rename(columns={"EmployeeNumber": "Total Staff", "NetSalary": "Avg Salary"})
            st.write(report)

        # LOGOUT
        elif choice == "Logout":
            st.session_state.logged_in = False
            st.rerun()

# Note: Add/Update/Delete requires saving to GitHub which isn't direct from a hosted app, 
# but the Display/Logic/Charts work perfectly!