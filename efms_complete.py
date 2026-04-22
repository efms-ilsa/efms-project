import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os
import json
import logging
from datetime import datetime
import hashlib
import shutil

# ────────────────────────── COLORS ──────────────────────────

class Color:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def success(msg): print(f"{Color.GREEN}OK   {msg}{Color.RESET}")
def error(msg):   print(f"{Color.RED}ERR  {msg}{Color.RESET}")
def info(msg):    print(f"{Color.CYAN}>>   {msg}{Color.RESET}")
def warn(msg):    print(f"{Color.YELLOW}!!   {msg}{Color.RESET}")

def header(msg):
    print(f"\n{Color.BOLD}{Color.CYAN}")
    print("=" * 50)
    print(f"  {msg}")
    print("=" * 50)
    print(Color.RESET, end="")

# ────────────────────────── LOGGING ──────────────────────────

logging.basicConfig(
    filename="efms_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
def log(message):
    logging.info(message)


# ────────────────────────── CONFIG FILE ──────────────────────────

CONFIG_FILE = "efms_config.json"
DEFAULT_CONFIG = {
    "bonus_rate": 0.10,
    "deduction_rate": 0.05,
    "data_file": "employee_data.csv",
    "backup_folder": "backups",
    "max_login_attempts": 3
}

def load_config():     #make sure that config file exists then read it 
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
    with open(CONFIG_FILE) as f:
        return json.load(f)

CFG = load_config()


# ────────────────────────── USERS FILE ──────────────────────────

USERS_FILE = "efms_users.json"

DEFAULT_USERS = {
    "admin":  {"password": hashlib.sha256("admin123".encode()).hexdigest(), "role": "Admin"},
    "hr":     {"password": hashlib.sha256("hr1234".encode()).hexdigest(),   "role": "HR"},
    "viewer": {"password": hashlib.sha256("view123".encode()).hexdigest(),  "role": "Viewer"}
}

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f, indent=4)
    with open(USERS_FILE) as f:
        return json.load(f)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ────────────────────────── LOGIN ──────────────────────────

def login():
    header("EMPLOYEE & FINANCE MANAGEMENT SYSTEM")
    print(f"\n  Default logins:")
    print(f"  Username: admin    Password: admin123")
    print(f"  Username: hr       Password: hr1234")
    print(f"  Username: viewer   Password: view123\n")

    users = load_users()
    max_attempts = CFG.get("max_login_attempts", 3)

    for attempt in range(1, max_attempts + 1):
        username = input("  Username: ").strip()
        password = input("  Password: ").strip()

        if username in users and users[username]["password"] == hash_password(password):
            role = users[username]["role"]
            success(f"Login successful! Welcome {username} [{role}]")
            log(f"LOGIN SUCCESS | user={username} | role={role}")
            return username, role
        else:
            remaining = max_attempts - attempt
            error(f"Wrong credentials. {remaining} attempt(s) left.")
            log(f"LOGIN FAILED | user={username} | attempt={attempt}")

    error("Too many failed attempts. Exiting.")
    return None, None


# ────────────────────────── BACKUP ──────────────────────────

def backup_data():  # make automatic copies of entire csv file
    folder = CFG.get("backup_folder", "backups")
    os.makedirs(folder, exist_ok=True)
    src = CFG.get("data_file", "employee_data.csv")
    if os.path.exists(src):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(folder, f"backup_{timestamp}.csv")
        shutil.copy(src, dest)


# ────────────────────────── AUDIT LOG ──────────────────────────
AUDIT_FILE = "efms_audit.txt"   # add, delete, update

def audit(username, action, detail=""):  
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] USER={username} | ACTION={action} | {detail}\n"
    with open(AUDIT_FILE, "a") as f:
        f.write(entry)

# ────────────────────────── LOAD DATA ──────────────────────────

def load_data(): # open csv file and loads all data into data frames
    filepath = CFG.get("data_file", "employee_data.csv")
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        error(f"File not found: {filepath}")
        info("Creating blank employee file...")
        df = pd.DataFrame(columns=[
            "EmployeeNumber", "Department", "JobRole",
            "MonthlyIncome", "PerformanceRating", "YearsAtCompany",
            "Bonus", "Deduction", "NetSalary", "PerformanceScore"
        ])
        df.to_csv(filepath, index=False)
        return df

    b = CFG.get("bonus_rate", 0.10)
    d = CFG.get("deduction_rate", 0.05)

    if "Bonus"      not in df.columns: df["Bonus"]      = df["MonthlyIncome"] * b
    if "Deduction"  not in df.columns: df["Deduction"]  = df["MonthlyIncome"] * d
    if "NetSalary"  not in df.columns: df["NetSalary"]  = df["MonthlyIncome"] + df["Bonus"] - df["Deduction"]
    if "PerformanceScore" not in df.columns: df["PerformanceScore"] = 0

    return df

# ────────────────────────── SAVE DATA ──────────────────────────

def save_data(df, username="system"):
    backup_data()
    filepath = CFG.get("data_file", "employee_data.csv")
    try:
        df.to_csv(filepath, index=False)
        success("Data saved.")
        log(f"Data saved by {username}")
    except Exception as e:
        error(f"Save failed: {e}")


# ────────────────────────── SAFE INPUT HELPERS ──────────────────────────

def get_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            error("Enter a valid whole number.")

def get_float(prompt):
    while True:
        try:
            val = float(input(prompt).strip())
            if val < 0:
                error("Cannot be negative.")
                continue
            return val
        except ValueError:
            error("Enter a valid number.")

def get_rating(prompt):
    while True:
        val = get_int(prompt)
        if 1 <= val <= 5:
            return val
        error("Rating must be 1 to 5.")


# ────────────────────────── SHOW EMPLOYEES (10 at a time) ──────────────────────────

def show_employees(df):
    header("ALL EMPLOYEES")
    if df.empty:
        warn("No employees found.")
        return
    page_size = 10
    total = len(df)
    pages = (total + page_size - 1) // page_size
    for page in range(pages):
        chunk = df.iloc[page * page_size:(page + 1) * page_size]
        print(chunk.to_string(index=False))
        info(f"Page {page+1}/{pages}  |  Total: {total} employees")
        if page < pages - 1:
            cont = input("  Press Enter for next page, or q to quit: ").strip().lower()
            if cont == "q":
                break

# ────────────────────────── SEARCH ──────────────────────────
def search_employee(df):
    header("SEARCH EMPLOYEE")
    emp_id = get_int("  Enter Employee ID: ")
    result = df[df["EmployeeNumber"] == emp_id]
    if result.empty:
        error(f"No employee found with ID {emp_id}.")
    else:
        print(result.to_string(index=False))

# ────────────────────────── ADD EMPLOYEE ──────────────────────────

def add_employee(df, username):
    header("ADD EMPLOYEE")
    emp_id = get_int("  Employee ID: ")
    if emp_id in df["EmployeeNumber"].values:
        error(f"ID {emp_id} already exists. Use Update instead.")
        return df

    dept       = input("  Department: ").strip()
    job_role   = input("  Job Role: ").strip()
    salary     = get_float("  Monthly Salary (USD): ")
    rating     = get_rating("  Performance Rating (1-5): ")
    years      = get_int("  Years at Company: ")
    perf_score = get_float("  Performance Score: ")

    b = CFG.get("bonus_rate", 0.10)
    d = CFG.get("deduction_rate", 0.05)

    bonus     = round(salary * b, 2)
    deduction = round(salary * d, 2)
    net       = round(salary + bonus - deduction, 2)

    new_row = {
        "EmployeeNumber": emp_id, "Department": dept, "JobRole": job_role,
        "MonthlyIncome": salary, "PerformanceRating": rating,
        "YearsAtCompany": years, "Bonus": bonus,
        "Deduction": deduction, "NetSalary": net, "PerformanceScore": perf_score
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df, username)
    audit(username, "ADD", f"ID={emp_id}, Dept={dept}, Salary={salary}")
    success(f"Employee {emp_id} added.")
    return df


# ────────────────────────── UPDATE EMPLOYEE ──────────────────────────

def update_employee(df, username):
    header("UPDATE EMPLOYEE")
    emp_id = get_int("  Employee ID to update: ")
    index  = df[df["EmployeeNumber"] == emp_id].index
    if len(index) == 0:
        error(f"ID {emp_id} not found.")
        return df

    print("  1. Monthly Salary")
    print("  2. Performance Rating")
    print("  3. Years at Company")
    print("  4. Department / Job Role")
    choice = input("  What to update? ").strip()

    b = CFG.get("bonus_rate", 0.10)
    d = CFG.get("deduction_rate", 0.05)

    if choice == "1":
        salary = get_float("  New Monthly Salary (USD): ")
        df.loc[index, "MonthlyIncome"] = salary
        df.loc[index, "Bonus"]         = round(salary * b, 2)
        df.loc[index, "Deduction"]     = round(salary * d, 2)
        df.loc[index, "NetSalary"]     = round(salary + salary*b - salary*d, 2)
        audit(username, "UPDATE_SALARY", f"ID={emp_id}, Salary={salary}")
    elif choice == "2":
        rating = get_rating("  New Rating (1-5): ")
        df.loc[index, "PerformanceRating"] = rating
        audit(username, "UPDATE_RATING", f"ID={emp_id}, Rating={rating}")
    elif choice == "3":
        years = get_int("  New Years at Company: ")
        df.loc[index, "YearsAtCompany"] = years
        audit(username, "UPDATE_YEARS", f"ID={emp_id}, Years={years}")
    elif choice == "4":
        dept     = input("  New Department: ").strip()
        job_role = input("  New Job Role: ").strip()
        df.loc[index, "Department"] = dept
        df.loc[index, "JobRole"]    = job_role
        audit(username, "UPDATE_DEPT", f"ID={emp_id}, Dept={dept}")
    else:
        error("Invalid choice.")
        return df

    save_data(df, username)
    success("Employee updated.")
    return df


# ────────────────────────── DELETE EMPLOYEE ──────────────────────────

def delete_employee(df, username):
    header("DELETE EMPLOYEE")
    emp_id = get_int("  Employee ID to delete: ")
    if emp_id not in df["EmployeeNumber"].values:
        error(f"ID {emp_id} not found.")
        return df
    confirm = input(f"  Are you sure? Type YES to confirm: ").strip()
    if confirm != "YES":
        info("Deletion cancelled.")
        return df
    df = df[df["EmployeeNumber"] != emp_id].reset_index(drop=True)
    save_data(df, username)
    audit(username, "DELETE", f"ID={emp_id}")
    success(f"Employee {emp_id} deleted.")
    return df

# ────────────────────────── TOP SALARIES ──────────────────────────

def top_salaries(df):
    header("TOP 5 HIGHEST PAID EMPLOYEES")
    if df.empty:
        warn("No data available.")
        return
    cols = [c for c in ["EmployeeNumber","Department","JobRole","NetSalary"] if c in df.columns]
    print(df.sort_values("NetSalary", ascending=False)[cols].head(5).to_string(index=False))


# ────────────────────────── DASHBOARD ──────────────────────────

def dashboard(df):
    header("DASHBOARD")
    if df.empty:
        warn("No data to display.")
        return

    print(f"\n  Total Employees   : {len(df)}")
    print(f"  Average Net Salary: ${df['NetSalary'].mean():,.2f}")
    print(f"  Highest Net Salary: ${df['NetSalary'].max():,.2f}")
    print(f"  Lowest Net Salary : ${df['NetSalary'].min():,.2f}")
    print(f"  Total Bonus Paid  : ${df['Bonus'].sum():,.2f}")
    print(f"  Avg Performance   : {df['PerformanceRating'].mean():.2f} / 5\n")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("EFMS Dashboard", fontsize=16, fontweight="bold")

    axes[0,0].hist(df["NetSalary"], bins=20, color="#4A90D9", edgecolor="white")
    axes[0,0].set_title("Salary Distribution")
    axes[0,0].set_xlabel("Net Salary (USD)")
    axes[0,0].set_ylabel("Employees")

    if "Department" in df.columns:
        dept_salary = df.groupby("Department")["NetSalary"].mean().sort_values(ascending=False)
        dept_salary.plot(kind="bar", ax=axes[0,1], color="#E67E22", edgecolor="white")
        axes[0,1].set_title("Avg Salary by Department")
        axes[0,1].tick_params(axis="x", rotation=30)

    if "Department" in df.columns:
        dept_count = df["Department"].value_counts()
        axes[1,0].pie(dept_count, labels=dept_count.index, autopct="%1.1f%%", startangle=140)
        axes[1,0].set_title("Employees by Department")

    if "PerformanceRating" in df.columns:
        rating_count = df["PerformanceRating"].value_counts().sort_index()
        rating_count.plot(kind="bar", ax=axes[1,1], color="#2ECC71", edgecolor="white")
        axes[1,1].set_title("Performance Rating Distribution")
        axes[1,1].tick_params(axis="x", rotation=0)

    plt.tight_layout()
    plt.savefig("efms_dashboard.png", dpi=150)
    plt.show()
    info("Dashboard saved as efms_dashboard.png")


# ────────────────────────── SALARY PREDICTION ──────────────────────────

def prediction(df):
    header("SALARY PREDICTION")
    if df.empty:
        warn("Not enough data.")
        return

    features = [c for c in ["YearsAtCompany","PerformanceRating","PerformanceScore"] if c in df.columns]
    df_clean = df[features + ["NetSalary"]].dropna()

    if len(df_clean) < 10:
        warn("Need at least 10 employees for prediction.")
        return

    X = df_clean[features]
    y = df_clean["NetSalary"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    joblib.dump(model, "efms_model.pkl")

    y_pred = model.predict(X_test)
    info(f"Model Accuracy (R2): {r2_score(y_test, y_pred):.2%}")
    info(f"Average Error (MAE): ${mean_absolute_error(y_test, y_pred):,.2f}")

    print()
    input_vals = []
    for feat in features:
        val = get_float(f"  Enter {feat}: ")
        input_vals.append(val)

    predicted = model.predict([input_vals])[0]
    success(f"Predicted Net Salary: ${predicted:,.2f}")


# ────────────────────────── ATTENDANCE TRACKER ──────────────────────────

def attendance_tracker(df):
    header("ATTENDANCE TRACKER")
    emp_id = get_int("  Employee ID: ")
    result = df[df["EmployeeNumber"] == emp_id]
    if result.empty:
        error(f"ID {emp_id} not found.")
        return

    salary   = result.iloc[0]["MonthlyIncome"]
    dept     = result.iloc[0].get("Department", "N/A")
    job_role = result.iloc[0].get("JobRole", "N/A")

    info(f"Employee: {emp_id} | {dept} | {job_role}")
    info(f"Monthly Salary: ${salary:,.2f}")

    total_days  = get_int("  Total working days this month: ")
    if total_days <= 0:
        error("Must be greater than 0.")
        return
    days_worked = get_int("  Days actually worked: ")
    if days_worked > total_days:
        error("Cannot exceed total days.")
        return

    absent          = total_days - days_worked
    rate            = (days_worked / total_days) * 100
    adj_salary      = salary * (days_worked / total_days)
    b               = CFG.get("bonus_rate", 0.10)
    d               = CFG.get("deduction_rate", 0.05)
    adj_net         = adj_salary + adj_salary*b - adj_salary*d

    print(f"\n  Days Worked      : {days_worked}")
    print(f"  Days Absent      : {absent}")
    print(f"  Attendance Rate  : {rate:.1f}%")
    print(f"  Adjusted Salary  : ${adj_salary:,.2f}")

    if rate < 75:
        warn(f"  Final Net Pay    : ${adj_net:,.2f}  [Below 75% attendance]")
    else:
        success(f"  Final Net Pay    : ${adj_net:,.2f}")


# ────────────────────────── DEPARTMENT REPORT ──────────────────────────

def department_report(df):
    header("DEPARTMENT REPORT")
    if df.empty or "Department" not in df.columns:
        warn("No data available.")
        return
    report = df.groupby("Department").agg(
        Employees     =("EmployeeNumber", "count"),
        Avg_Salary    =("NetSalary", "mean"),
        Total_Payroll =("NetSalary", "sum"),
        Avg_Rating    =("PerformanceRating", "mean"),
        Avg_Years     =("YearsAtCompany", "mean")
    ).round(2)
    print(report.to_string())


# ────────────────────────── VIEW AUDIT LOG ──────────────────────────

def view_audit():
    header("AUDIT LOG (Last 20 entries)")
    if not os.path.exists(AUDIT_FILE):
        warn("No audit log yet.")
        return
    with open(AUDIT_FILE) as f:
        lines = f.readlines()
    for line in lines[-20:]:
        print(" ", line.strip())


# ──────────────────────────PERMISSIONS──────────────────────────

ROLE_PERMISSIONS = {
    "Admin" : ["1","2","3","4","5","6","7","8","9","10","11","12"],
    "HR"    : ["1","2","3","4","6","7","8","9","10","11","12"],
    "Viewer": ["1","2","6","8","9","10"]
}

def allowed(role, choice):
    return choice in ROLE_PERMISSIONS.get(role, [])

# ──────────────────MAIN MENU────────────────

def main(username, role):
    df = load_data()

    while True:
        header(f"EFMS MENU  |  User: {username}  |  Role: {role}")
        print(f"  {'1'}.  Show Employees")
        print(f"  {'2'}.  Search Employee")
        print(f"  {'3'}.  Add Employee        {'[Admin/HR only]' if role == 'Viewer' else ''}")
        print(f"  {'4'}.  Update Employee     {'[Admin/HR only]' if role == 'Viewer' else ''}")
        print(f"  {'5'}.  Delete Employee     {'[Admin only]' if role != 'Admin' else ''}")
        print(f"  {'6'}.  Dashboard")
        print(f"  {'7'}.  Salary Prediction   {'[Admin/HR only]' if role == 'Viewer' else ''}")
        print(f"  {'8'}.  Top 5 Salaries")
        print(f"  {'9'}.  Attendance Tracker")
        print(f"  {'10'}. Department Report")
        print(f"  {'11'}. View Audit Log      {'[Admin only]' if role != 'Admin' else ''}")
        print(f"  {'12'}. Exit")

        choice = input(f"\n  Enter choice: ").strip()

        if not allowed(role, choice):
            error("You do not have permission for this.")
            continue

        if   choice == "1":  show_employees(df)
        elif choice == "2":  search_employee(df)
        elif choice == "3":  df = add_employee(df, username)
        elif choice == "4":  df = update_employee(df, username)
        elif choice == "5":  df = delete_employee(df, username)
        elif choice == "6":  dashboard(df)
        elif choice == "7":  prediction(df)
        elif choice == "8":  top_salaries(df)
        elif choice == "9":  attendance_tracker(df)
        elif choice == "10": department_report(df)
        elif choice == "11": view_audit()
        elif choice == "12":
            success("Goodbye!")
            audit(username, "LOGOUT")
            break
        else:
            error("Invalid option. Enter a number from 1 to 12.")

# ────────────────────────── START ──────────────────────────
if __name__ == "__main__":
    username, role = login()
    if username:
        main(username, role)