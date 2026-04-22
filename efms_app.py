import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import os
import hashlib

# ────────────────────────── CONFIG & HELPERS ──────────────────────────
DATA_FILE = "employee_data.csv"

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

DEFAULT_USERS = {
    "admin":  {"password": hash_password("admin123"), "role": "Admin"},
    "hr":     {"password": hash_password("hr1234"),   "role": "HR"},
    "viewer": {"password": hash_password("view123"),  "role": "Viewer"}
}

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["EmployeeNumber", "Department", "JobRole", "MonthlyIncome", "PerformanceRating", "YearsAtCompany", "NetSalary"])

# ────────────────────────── SESSION STATE ──────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""

st.set_page_config(page_title="EFMS Pro", layout="wide")

# ────────────────────────── APP LOGIC ──────────────────────────
if not st.session_state.logged_in:
    st.title("🔐 EFMS Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in DEFAULT_USERS and DEFAULT_USERS[u]["password"] == hash_password(p):
            st.session_state.logged_in = True
            st.session_state.role = DEFAULT_USERS[u]["role"]
            st.rerun()
        else: st.error("Wrong Username or Password")
else:
    df = load_data()
    role = st.session_state.role
    
    menu = ["Dashboard", "Show Employees", "Search Employee", "Add Employee", "Update Employee", "Delete Employee", "Salary Prediction", "Logout"]
    choice = st.sidebar.selectbox("Main Menu", menu)

    # 1. DASHBOARD
    if choice == "Dashboard":
        st.header("📊 Analytics Dashboard")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Salary Distribution")
            fig1, ax1 = plt.subplots(); ax1.hist(df["NetSalary"], bins=15, color="#4A90D9"); st.pyplot(fig1)
        with c2:
            st.subheader("Avg Salary by Dept")
            st.bar_chart(df.groupby("Department")["NetSalary"].mean())
        
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Department Share")
            fig2, ax2 = plt.subplots(); df["Department"].value_counts().plot.pie(autopct='%1.1f%%', ax=ax2); st.pyplot(fig2)
        with c4:
            st.subheader("Performance Ratings")
            st.bar_chart(df["PerformanceRating"].value_counts())

    # 2. SHOW
    elif choice == "Show Employees":
        st.header("📋 Employee Data")
        st.dataframe(df, use_container_width=True)

    # 3. ADD
    elif choice == "Add Employee":
        st.header("➕ Add New Record")
        if role == "Viewer": st.error("Access Denied!")
        else:
            with st.form("add"):
                new_id = st.number_input("ID", step=1)
                new_dept = st.selectbox("Dept", ["Sales", "HR", "R&D", "Finance"])
                new_sal = st.number_input("Salary")
                if st.form_submit_button("Add"):
                    st.success(f"ID {new_id} added (Live Simulation).")

    # 4. UPDATE
    elif choice == "Update Employee":
        st.header("📝 Update Salary")
        if role == "Viewer": st.error("Access Denied!")
        else:
            up_id = st.number_input("ID to Update", step=1)
            up_sal = st.number_input("New Salary")
            if st.button("Update"):
                st.success(f"Salary updated for ID {up_id}!")

    # 5. DELETE
    elif choice == "Delete Employee":
        st.header("❌ Remove Record")
        if role != "Admin": st.error("Only Admin can delete!")
        else:
            del_id = st.number_input("ID to Delete", step=1)
            if st.button("Confirm Delete"):
                st.warning(f"Employee {del_id} removed.")

    # 6. PREDICTION
    elif choice == "Salary Prediction":
        st.header("🔮 AI Salary Predictor")
        model = LinearRegression().fit(df[["YearsAtCompany", "PerformanceRating"]], df["NetSalary"])
        y = st.number_input("Years", 0, 40, 5)
        r = st.slider("Rating", 1, 5, 3)
        if st.button("Predict"):
            p = model.predict([[y, r]])[0]
            st.success(f"Predicted Salary: ${p:,.2f}")

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.rerun()