# 📚 Smart Attendance Management System

A robust, full-stack institutional prototype engineered in Python and Streamlit (backed by SQLAlchemy and SQLite) to manage attendance operations for large-scale academic environments (designed for 5,000+ students and 200+ faculty members). 

## ✨ Key Features

1. **Role-Based Access Control (RBAC):**
   * Secure session-managed authentication partitioned across three distinct user roles: **Admin**, **Faculty**, and **Student**.

2. **Admin Master Governance:**
   * Full management dashboards for Departments, Classes, Sections, Faculty/Student onboarding, and Subject mappings.
   * Centralized **Attendance Correction Review Panel** to Approve or Reject pending tickets with an immutable audit history trail.

3. **Faculty Operations & Corrections:**
   * Session-based date and period attendance logging (`PRESENT`, `ABSENT`, `LATE`) for assigned sections.
   * Built-in correction ticketing system to request modifications with mandatory justification reasons.

4. **Student Analytics & Compliance:**
   * Real-time subject-wise performance dashboards calculating precise attendance metrics and status counts.
   * Automated visual warnings and threshold alerts for students falling below the mandatory **75% institutional compliance threshold**.
   * Transparent audit views displaying the status of any requested attendance corrections.

---

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Frontend/UI:** Streamlit
* **Database & ORM:** SQLite & SQLAlchemy ORM
* **Security:** Secure password hashing

---

## 🚀 Getting Started Locally

Follow these instructions to run the project locally on your machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/Smart-Attendance-Management.git](https://github.com/your-username/Smart-Attendance-Management.git)
cd Smart-Attendance-Management
2. Create and Activate a Virtual Environment
Bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
3. Install Dependencies
Bash
pip install -r requirements.txt
4. Run the Application
Bash
streamlit run app.py
👥 Default User Roles & Workflow
Admin: Manages master academic structure, user accounts, subject assignments, and audits correction requests.

Faculty: Marks daily class attendance and submits correction tickets if entry mistakes occur.

Student: Views subject-wise percentage metrics, detailed session histories, and low-attendance warnings.
