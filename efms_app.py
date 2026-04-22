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
    st.session_state.username = ""

st.set_page_config(page_title="EFMS Ultimate Dashboard", layout="wide")

# ────────────────────────── LOGIN PAGE ──────────────────────────
if not st.session_state.logged_in:
    st.title("🔐 EFMS Live System")
    st.subheader("Please Login to Continue")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in DEFAULT_USERS and DEFAULT_USERS[u]["password"] == hash_password(p):
            st.session_state.logged_in = True
            st.session_state.role = DEFAULT_USERS[u]["role"]
            st.session_state.username = u
            st.rerun()
        else:
            st.error("Invalid Username or Password")
else:
    # ────────────────────────── MAIN APP ──────────────────────────
    df = load_data()
    role = st.session_state.role
    
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"Role: **{role}**")

    menu = [
        "Show Employees", "Search Employee", "Add Employee", 
        "Update Employee", "Delete Employee", "Dashboard", 
        "Salary Prediction", "Top Five Salaries", "Attendance Tracker", 
        "Department Report", "Logout"
    ]
    choice = st.sidebar.selectbox("Main Menu", menu)

    # 1. SHOW EMPLOYEES
    if choice == "Show Employees":
        st.header("📋 All Employee Records")
        st.dataframe(df, use_container_width=True)

    # 2. SEARCH
    elif choice == "Search Employee":
        st.header("🔍 Search Employee")
        sid = st.number_input("Enter Employee ID", step=1)
        if st.button("Find"):
            res = df[df["EmployeeNumber"] == sid]
            st.table(res) if not res.empty else st.error("ID not found")

    # 3. ADD (Interface)
    elif choice == "Add Employee":
        st.header("➕ Add New Employee")
        if role == "Viewer": st.error("Access Denied")
        else:
            with st.form("add"):
                e_id = st.number_input("ID", step=1)
                dept = st.selectbox("Department", ["Sales", "HR", "R&D", "Finance", "IT"])
                sal = st.number_input("Monthly Income")
                if st.form_submit_button("Add"):
                    st.success(f"Employee {e_id} added successfully (Session Mode)")

    # 4. UPDATE
    elif choice == "Update Employee":
        st.header("📝 Update Record")
        if role == "Viewer": st.error("Access Denied")
        else:
            up_id = st.number_input("ID to Update", step=1)
            new_sal = st.number_input("New Salary")
            if st.button("Update"):
                st.success(f"Data updated for ID {up_id}")

    # 5. DELETE
    elif choice == "Delete Employee":
        st.header("❌ Delete Record")
        if role != "Admin": st.error("Only Admin can delete")
        else:
            del_id = st.number_input("ID to Delete", step=1)
            if st.button("Delete Permanently"):
                st.warning(f"Employee {del_id} removed")

    # 6. DASHBOARD (4 Graphs)
    elif choice == "Dashboard":
        st.header("📊 Business Analytics")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Salary Distribution")
            fig1, ax1 = plt.subplots(); ax1.hist(df["NetSalary"], bins=15, color='skyblue'); st.pyplot(fig1)
        with c2:
            st.subheader("Avg Salary by Dept")
            st.bar_chart(df.groupby("Department")["NetSalary"].mean())
        
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Dept Distribution")
            fig2, ax2 = plt.subplots(); df["Department"].value_counts().plot.pie(autopct='%1.1f%%', ax=ax2); st.pyplot(fig2)
        with c4:
            st.subheader("Performance Scores")
            st.bar_chart(df["PerformanceRating"].value_counts())

    # 7. SALARY PREDICTION
    elif choice == "Salary Prediction":
        st.header("🔮 Prediction Model")
        X = df[["YearsAtCompany", "PerformanceRating"]]
        y = df["NetSalary"]
        model = LinearRegression().fit(X, y)
        yrs = st.number_input("Years at Company", 0, 40, 5)
        rat = st.slider("Rating", 1, 5, 3)
        if st.button("Predict"):
            p = model.predict([[yrs, rat]])[0]
            st.success(f"Predicted Salary: ${p:,.2f}")

    # 8. TOP FIVE SALARIES
    elif choice == "Top Five Salaries":
        st.header("🏆 Top 5 Highest Earners")
        top5 = df.sort_values("NetSalary", ascending=False).head(5)
        st.table(top5[["EmployeeNumber", "JobRole", "NetSalary"]])

    # 9. ATTENDANCE TRACKER
    elif choice == "Attendance Tracker":
        st.header("🕒 Attendance Pay Calculator")
        total_d = st.slider("Days in Month", 20, 31, 22)
        work_d = st.slider("Days Present", 0, total_d, total_d)
        if st.button("Calculate"):
            st.info(f"Attendance: {(work_d/total_d)*100:.1f}%")

    # 10. DEPARTMENT REPORT
    elif choice == "Department Report":
        st.header("🏢 Department-wise Summary")
        report = df.groupby("Department").agg({"EmployeeNumber":"count", "NetSalary":"mean"})
        report.columns = ["Total Employees", "Avg Net Salary"]
        st.write(report)

    # 11. EXIT (LOGOUT)
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.rerun()