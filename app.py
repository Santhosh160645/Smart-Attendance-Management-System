# ```python
# print("All database tables created successfully")

import streamlit as st
from datetime import date, datetime

from database.db import Base, SessionLocal, engine
from models.models import (
    User,
    Department,
    Class,
    Section,
    Student,
    Faculty,
    Subject,
    FacultySubject,
    Enrollment,
    ClassSession,
    Attendance,
    AttendanceCorrection,
    AuditLog,
)
from services.auth_service import authenticate_user
from services.setup_service import create_initial_admin
from services.correction_service import (
    request_correction,
    review_correction,
)

# --------------------------------------------------
# Create database tables
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


def get_db():
    return SessionLocal()


st.set_page_config(
    page_title="Smart Attendance Management",
    page_icon="📚",
    layout="wide"
)


# --------------------------------------------------
# Session State
# --------------------------------------------------

if "user" not in st.session_state:
    st.session_state.user = None


# --------------------------------------------------
# Initial Setup
# --------------------------------------------------

db = get_db()

admin_exists = (
    db.query(User)
    .filter(User.role == "ADMIN")
    .first()
    is not None
)

if not admin_exists:

    st.title("📚 Smart Attendance Management System")

    st.subheader("Initial System Setup")

    st.info(
        "No administrator account exists yet. "
        "Create the first administrator account to continue."
    )

    with st.form("initial_admin_form"):

        username = st.text_input(
            "Administrator Username"
        )

        password = st.text_input(
            "Administrator Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Create Administrator"
        )

        if submitted:

            if not username.strip():

                st.error(
                    "Username is required."
                )

            elif not password:

                st.error(
                    "Password is required."
                )

            elif len(password) < 8:

                st.error(
                    "Password must contain at least 8 characters."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                success, message = create_initial_admin(
                    db,
                    username.strip(),
                    password
                )

                if success:

                    st.success(message)
                    st.rerun()

                else:

                    st.error(message)

    db.close()
    st.stop()


# --------------------------------------------------
# Login Screen
# --------------------------------------------------

if st.session_state.user is None:

    st.title("📚 Smart Attendance Management System")

    st.subheader("Login")

    with st.form("login_form"):

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Login"
        )

        if submitted:

            if not username.strip() or not password:

                st.error(
                    "Please enter username and password."
                )

            else:

                user = authenticate_user(
                    db,
                    username.strip(),
                    password
                )

                if user:

                    st.session_state.user = {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role
                    }

                    st.rerun()

                else:

                    st.error(
                        "Invalid username or password."
                    )

    db.close()
    st.stop()


# --------------------------------------------------
# Logged-in User
# --------------------------------------------------

user = st.session_state.user

st.sidebar.title(
    "Smart Attendance"
)

st.sidebar.write(
    f"**User:** {user['username']}"
)

st.sidebar.write(
    f"**Role:** {user['role']}"
)

if st.sidebar.button("Logout"):

    st.session_state.user = None
    st.rerun()


# ==================================================
# ADMIN DASHBOARD
# ==================================================

if user["role"] == "ADMIN":

    st.title(
        "👨‍💼 Admin Dashboard"
    )

    # ------------------------------------------
    # Department Management
    # ------------------------------------------

    st.subheader(
        "Department Management"
    )

    tab1, tab2 = st.tabs(
        [
            "Add Department",
            "View Departments"
        ]
    )

    # ------------------------------------------
    # Add Department
    # ------------------------------------------

    with tab1:

        with st.form(
            "add_department_form"
        ):

            department_name = st.text_input(
                "Department Name"
            )

            department_code = st.text_input(
                "Department Code"
            )

            submitted = st.form_submit_button(
                "Add Department"
            )

            if submitted:

                department_name = (
                    department_name.strip()
                )

                department_code = (
                    department_code.strip().upper()
                )

                if not department_name:

                    st.error(
                        "Department name is required."
                    )

                elif not department_code:

                    st.error(
                        "Department code is required."
                    )

                else:

                    existing = (
                        db.query(Department)
                        .filter(
                            (Department.name == department_name)
                            |
                            (
                                Department.code
                                == department_code
                            )
                        )
                        .first()
                    )

                    if existing:

                        st.error(
                            "Department name or code already exists."
                        )

                    else:

                        department = Department(
                            name=department_name,
                            code=department_code
                        )

                        db.add(department)
                        db.commit()
                        db.refresh(department)

                        st.success(
                            f"Department '{department.name}' "
                            "added successfully."
                        )

    # ------------------------------------------
    # View Departments
    # ------------------------------------------

    with tab2:

        departments = (
            db.query(Department)
            .order_by(Department.name)
            .all()
        )

        if not departments:

            st.info(
                "No departments have been added yet."
            )

        else:

            st.write(
                f"Total Departments: {len(departments)}"
            )

            for department in departments:

                st.write(
                    f"**{department.code}** — "
                    f"{department.name}"
                )

    # ------------------------------------------
    # Class & Section Management
    # ------------------------------------------

    st.divider()

    st.subheader(
        "Class & Section Management"
    )

    class_tab1, class_tab2, class_tab3 = st.tabs(
        [
            "Add Class",
            "Add Section",
            "View Classes & Sections"
        ]
    )

    # ------------------------------------------
    # Add Class
    # ------------------------------------------

    with class_tab1:

        departments = (
            db.query(Department)
            .order_by(Department.name)
            .all()
        )

        if not departments:

            st.warning(
                "Please create a department first."
            )

        else:

            department_options = {
                f"{department.code} - {department.name}":
                    department
                for department in departments
            }

            with st.form(
                "add_class_form"
            ):

                selected_department = st.selectbox(
                    "Department",
                    list(
                        department_options.keys()
                    )
                )

                class_name = st.text_input(
                    "Class Name",
                    placeholder="Example: B.Tech CSE"
                )

                year = st.selectbox(
                    "Year",
                    [1, 2, 3, 4]
                )

                submitted = st.form_submit_button(
                    "Add Class"
                )

                if submitted:

                    class_name = (
                        class_name.strip()
                    )

                    if not class_name:

                        st.error(
                            "Class name is required."
                        )

                    else:

                        department = (
                            department_options[
                                selected_department
                            ]
                        )

                        existing = (
                            db.query(Class)
                            .filter(
                                Class.name == class_name,
                                Class.year == year,
                                Class.department_id
                                == department.id
                            )
                            .first()
                        )

                        if existing:

                            st.error(
                                "This class already exists."
                            )

                        else:

                            new_class = Class(
                                name=class_name,
                                year=year,
                                department_id=department.id
                            )

                            db.add(new_class)
                            db.commit()
                            db.refresh(new_class)

                            st.success(
                                f"Class '{new_class.name}' "
                                f"(Year {new_class.year}) "
                                "created successfully."
                            )

    # ------------------------------------------
    # Add Section
    # ------------------------------------------

    with class_tab2:

        classes = (
            db.query(Class)
            .order_by(
                Class.name,
                Class.year
            )
            .all()
        )

        if not classes:

            st.warning(
                "Please create a class first."
            )

        else:

            class_options = {
                f"{item.name} - Year {item.year}":
                    item
                for item in classes
            }

            with st.form(
                "add_section_form"
            ):

                selected_class = st.selectbox(
                    "Class",
                    list(
                        class_options.keys()
                    )
                )

                section_name = st.text_input(
                    "Section Name",
                    placeholder="Example: A"
                )

                submitted = st.form_submit_button(
                    "Add Section"
                )

                if submitted:

                    section_name = (
                        section_name.strip().upper()
                    )

                    if not section_name:

                        st.error(
                            "Section name is required."
                        )

                    else:

                        selected_class_obj = (
                            class_options[
                                selected_class
                            ]
                        )

                        existing = (
                            db.query(Section)
                            .filter(
                                Section.name
                                == section_name,
                                Section.class_id
                                == selected_class_obj.id
                            )
                            .first()
                        )

                        if existing:

                            st.error(
                                "This section already exists "
                                "for the selected class."
                            )

                        else:

                            section = Section(
                                name=section_name,
                                class_id=selected_class_obj.id
                            )

                            db.add(section)
                            db.commit()
                            db.refresh(section)

                            st.success(
                                f"Section '{section.name}' "
                                "created successfully."
                            )

    # ------------------------------------------
    # View Classes & Sections
    # ------------------------------------------

    with class_tab3:

        classes = (
            db.query(Class)
            .order_by(
                Class.name,
                Class.year
            )
            .all()
        )

        if not classes:

            st.info(
                "No classes have been added yet."
            )

        else:

            for class_item in classes:

                department = (
                    db.query(Department)
                    .filter(
                        Department.id
                        == class_item.department_id
                    )
                    .first()
                )

                st.markdown(
                    f"### {class_item.name} "
                    f"— Year {class_item.year}"
                )

                st.write(
                    f"Department: "
                    f"{department.code if department else 'N/A'}"
                )

                sections = (
                    db.query(Section)
                    .filter(
                        Section.class_id
                        == class_item.id
                    )
                    .order_by(Section.name)
                    .all()
                )

                if sections:

                    section_names = [
                        section.name
                        for section in sections
                    ]

                    st.write(
                        "Sections: "
                        + ", ".join(section_names)
                    )

                else:

                    st.write(
                        "Sections: None"
                    )

    # ------------------------------------------
    # Faculty Management
    # ------------------------------------------

    st.divider()

    st.subheader(
        "Faculty Management"
    )

    faculty_tab1, faculty_tab2 = st.tabs(
        [
            "Add Faculty",
            "View Faculty"
        ]
    )

    # ------------------------------------------
    # Add Faculty
    # ------------------------------------------

    with faculty_tab1:

        departments = (
            db.query(Department)
            .order_by(Department.name)
            .all()
        )

        if not departments:

            st.warning(
                "Please create a department first."
            )

        else:

            department_options = {
                f"{department.code} - {department.name}":
                    department
                for department in departments
            }

            with st.form(
                "add_faculty_form"
            ):

                faculty_name = st.text_input(
                    "Faculty Name"
                )

                employee_id = st.text_input(
                    "Employee ID"
                )

                username = st.text_input(
                    "Login Username"
                )

                password = st.text_input(
                    "Login Password",
                    type="password"
                )

                selected_department = st.selectbox(
                    "Department",
                    list(
                        department_options.keys()
                    )
                )

                submitted = st.form_submit_button(
                    "Add Faculty"
                )

                if submitted:

                    faculty_name = (
                        faculty_name.strip()
                    )

                    employee_id = (
                        employee_id.strip()
                    )

                    username = (
                        username.strip()
                    )

                    if not faculty_name:

                        st.error(
                            "Faculty name is required."
                        )

                    elif not employee_id:

                        st.error(
                            "Employee ID is required."
                        )

                    elif not username:

                        st.error(
                            "Login username is required."
                        )

                    elif not password:

                        st.error(
                            "Login password is required."
                        )

                    elif len(password) < 8:

                        st.error(
                            "Password must contain "
                            "at least 8 characters."
                        )

                    else:

                        existing_user = (
                            db.query(User)
                            .filter(
                                User.username
                                == username
                            )
                            .first()
                        )

                        existing_faculty = (
                            db.query(Faculty)
                            .filter(
                                Faculty.employee_id
                                == employee_id
                            )
                            .first()
                        )

                        if existing_user:

                            st.error(
                                "Username already exists."
                            )

                        elif existing_faculty:

                            st.error(
                                "Employee ID already exists."
                            )

                        else:

                            department = (
                                department_options[
                                    selected_department
                                ]
                            )

                            from services.auth_service import (
                                hash_password
                            )

                            faculty_user = User(
                                username=username,
                                password_hash=hash_password(
                                    password
                                ),
                                role="FACULTY",
                                is_active=True
                            )

                            db.add(faculty_user)
                            db.flush()

                            faculty = Faculty(
                                user_id=faculty_user.id,
                                employee_id=employee_id,
                                name=faculty_name,
                                department_id=department.id
                            )

                            db.add(faculty)
                            db.commit()

                            st.success(
                                f"Faculty '{faculty_name}' "
                                "created successfully."
                            )

    # ------------------------------------------
    # View Faculty
    # ------------------------------------------

    with faculty_tab2:

        faculty_members = (
            db.query(Faculty)
            .order_by(Faculty.name)
            .all()
        )

        if not faculty_members:

            st.info(
                "No faculty members have been added yet."
            )

        else:

            st.write(
                f"Total Faculty: "
                f"{len(faculty_members)}"
            )

            for faculty in faculty_members:

                department = (
                    db.query(Department)
                    .filter(
                        Department.id
                        == faculty.department_id
                    )
                    .first()
                )

                user_account = (
                    db.query(User)
                    .filter(
                        User.id == faculty.user_id
                    )
                    .first()
                )

                st.write(
                    f"**{faculty.employee_id}** — "
                    f"{faculty.name}"
                )

                st.caption(
                    f"Department: "
                    f"{department.code if department else 'N/A'}"
                    f" | Username: "
                    f"{user_account.username if user_account else 'N/A'}"
                )

    # ------------------------------------------
    # Student Management
    # ------------------------------------------

    st.divider()

    st.subheader(
        "Student Management"
    )

    student_tab1, student_tab2 = st.tabs(
        [
            "Add Student",
            "View Students"
        ]
    )

    # ------------------------------------------
    # Add Student
    # ------------------------------------------

    with student_tab1:

        departments = (
            db.query(Department)
            .order_by(Department.name)
            .all()
        )

        if not departments:

            st.warning(
                "Please create a department first."
            )

        else:

            department_options = {
                f"{department.code} - {department.name}":
                    department
                for department in departments
            }

            with st.form(
                "add_student_form"
            ):

                student_name = st.text_input(
                    "Student Name"
                )

                roll_number = st.text_input(
                    "Roll Number"
                )

                username = st.text_input(
                    "Login Username"
                )

                password = st.text_input(
                    "Login Password",
                    type="password"
                )

                selected_department = st.selectbox(
                    "Department",
                    list(
                        department_options.keys()
                    )
                )

                selected_department_obj = (
                    department_options[
                        selected_department
                    ]
                )

                classes = (
                    db.query(Class)
                    .filter(
                        Class.department_id
                        == selected_department_obj.id
                    )
                    .order_by(
                        Class.name,
                        Class.year
                    )
                    .all()
                )

                if not classes:

                    st.warning(
                        "No classes found for this department. "
                        "Please create a class first."
                    )

                    selected_class_obj = None

                else:

                    class_options = {
                        f"{item.name} - Year {item.year}":
                            item
                        for item in classes
                    }

                    selected_class = st.selectbox(
                        "Class",
                        list(
                            class_options.keys()
                        )
                    )

                    selected_class_obj = (
                        class_options[
                            selected_class
                        ]
                    )

                if selected_class_obj:

                    sections = (
                        db.query(Section)
                        .filter(
                            Section.class_id
                            == selected_class_obj.id
                        )
                        .order_by(
                            Section.name
                        )
                        .all()
                    )

                    if not sections:

                        st.warning(
                            "No sections found for this class. "
                            "Please create a section first."
                        )

                        selected_section_obj = None

                    else:

                        section_options = {
                            section.name:
                                section
                            for section in sections
                        }

                        selected_section = st.selectbox(
                            "Section",
                            list(
                                section_options.keys()
                            )
                        )

                        selected_section_obj = (
                            section_options[
                                selected_section
                            ]
                        )

                else:

                    selected_section_obj = None

                submitted = st.form_submit_button(
                    "Add Student"
                )

                if submitted:

                    student_name = (
                        student_name.strip()
                    )

                    roll_number = (
                        roll_number.strip()
                    )

                    username = (
                        username.strip()
                    )

                    if not student_name:

                        st.error(
                            "Student name is required."
                        )

                    elif not roll_number:

                        st.error(
                            "Roll number is required."
                        )

                    elif not username:

                        st.error(
                            "Login username is required."
                        )

                    elif not password:

                        st.error(
                            "Login password is required."
                        )

                    elif len(password) < 8:

                        st.error(
                            "Password must contain "
                            "at least 8 characters."
                        )

                    elif not selected_class_obj:

                        st.error(
                            "Please create and select a class."
                        )

                    elif not selected_section_obj:

                        st.error(
                            "Please create and select a section."
                        )

                    else:

                        existing_user = (
                            db.query(User)
                            .filter(
                                User.username
                                == username
                            )
                            .first()
                        )

                        existing_student = (
                            db.query(Student)
                            .filter(
                                Student.roll_number
                                == roll_number
                            )
                            .first()
                        )

                        if existing_user:

                            st.error(
                                "Username already exists."
                            )

                        elif existing_student:

                            st.error(
                                "Roll number already exists."
                            )

                        else:

                            from services.auth_service import (
                                hash_password
                            )

                            student_user = User(
                                username=username,
                                password_hash=hash_password(
                                    password
                                ),
                                role="STUDENT",
                                is_active=True
                            )

                            db.add(student_user)
                            db.flush()

                            student = Student(
                                user_id=student_user.id,
                                roll_number=roll_number,
                                name=student_name,
                                department_id=(
                                    selected_department_obj.id
                                ),
                                class_id=(
                                    selected_class_obj.id
                                ),
                                section_id=(
                                    selected_section_obj.id
                                )
                            )

                            db.add(student)
                            db.commit()

                            st.success(
                                f"Student '{student_name}' "
                                "created successfully."
                            )

    # ------------------------------------------
    # View Students
    # ------------------------------------------

    with student_tab2:

        students = (
            db.query(Student)
            .order_by(Student.name)
            .all()
        )

        if not students:

            st.info(
                "No students have been added yet."
            )

        else:

            st.write(
                f"Total Students: {len(students)}"
            )

            for student in students:

                department = (
                    db.query(Department)
                    .filter(
                        Department.id
                        == student.department_id
                    )
                    .first()
                )

                class_item = (
                    db.query(Class)
                    .filter(
                        Class.id
                        == student.class_id
                    )
                    .first()
                )

                section = (
                    db.query(Section)
                    .filter(
                        Section.id
                        == student.section_id
                    )
                    .first()
                )

                user_account = (
                    db.query(User)
                    .filter(
                        User.id
                        == student.user_id
                    )
                    .first()
                )

                st.write(
                    f"**{student.roll_number}** — "
                    f"{student.name}"
                )

                st.caption(
                    f"Department: "
                    f"{department.code if department else 'N/A'}"
                    f" | Class: "
                    f"{class_item.name if class_item else 'N/A'}"
                    f" | Year: "
                    f"{class_item.year if class_item else 'N/A'}"
                    f" | Section: "
                    f"{section.name if section else 'N/A'}"
                    f" | Username: "
                    f"{user_account.username if user_account else 'N/A'}"
                )
        # ==================================================
        # Attendance Correction Management (Admin Review)
        # ==================================================

        st.divider()
        st.subheader("Attendance Correction Requests")

        pending_corrections = (
            db.query(AttendanceCorrection)
            .filter(AttendanceCorrection.status == "PENDING")
            .order_by(AttendanceCorrection.id.desc())
            .all()
        )

        if not pending_corrections:
            st.info("No pending attendance correction requests.")
        else:
            for correction in pending_corrections:
                attendance = db.query(Attendance).filter(Attendance.id == correction.attendance_id).first()
                faculty = db.query(Faculty).filter(Faculty.id == correction.requested_by).first()
                if not attendance:
                    continue

                session = db.query(ClassSession).filter(ClassSession.id == attendance.session_id).first()
                student = db.query(Student).filter(Student.id == attendance.student_id).first()
                subject = db.query(Subject).filter(Subject.id == session.subject_id).first() if session else None

                st.markdown("---")
                st.write(
                    f"**Student:** {student.name if student else 'Unknown'} ({student.roll_number if student else 'Unknown'})")
                st.write(f"**Subject:** {subject.code if subject else 'Unknown'}")
                st.write(
                    f"**Date:** {session.session_date.date() if session else 'Unknown'} | **Period:** {session.period if session else 'Unknown'}")
                st.write(f"**Requested By:** {faculty.name if faculty else 'Unknown'}")
                st.write(f"**Proposed Change:** {correction.old_status} → {correction.new_status}")
                st.write(f"**Reason:** {correction.reason}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{correction.id}"):
                        success, message = review_correction(
                            db=db,
                            correction_id=correction.id,
                            admin_user_id=user["id"],
                            decision="APPROVED",
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                with col2:
                    if st.button("Reject", key=f"reject_{correction.id}"):
                        success, message = review_correction(
                            db=db,
                            correction_id=correction.id,
                            admin_user_id=user["id"],
                            decision="REJECTED",
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        # ==================================================
        # Attendance Correction History
        # ==================================================

        st.divider()
        st.subheader("Attendance Correction History")

        correction_history = (
            db.query(AttendanceCorrection)
            .order_by(AttendanceCorrection.id.desc())
            .all()
        )

        if not correction_history:
            st.info("No attendance correction history available.")
        else:
            for correction in correction_history:
                attendance = db.query(Attendance).filter(Attendance.id == correction.attendance_id).first()
                faculty = db.query(Faculty).filter(Faculty.id == correction.requested_by).first()
                if not attendance:
                    continue

                session = db.query(ClassSession).filter(ClassSession.id == attendance.session_id).first()
                student = db.query(Student).filter(Student.id == attendance.student_id).first()
                subject = db.query(Subject).filter(Subject.id == session.subject_id).first() if session else None

                st.markdown("---")
                st.write(f"**Student:** {student.name if student else 'Unknown'}")
                st.write(f"**Roll Number:** {student.roll_number if student else 'Unknown'}")
                st.write(f"**Subject:** {subject.code if subject else 'Unknown'}")
                st.write(f"**Date:** {session.session_date.date() if session else 'Unknown'}")
                st.write(f"**Period:** {session.period if session else 'Unknown'}")
                st.write(f"**Requested By:** {faculty.name if faculty else 'Unknown'}")
                st.write(f"**Change:** {correction.old_status} → {correction.new_status}")
                st.write(f"**Reason:** {correction.reason}")
                st.write(f"**Request Status:** **{correction.status}**")
    # ------------------------------------------
    # Subject Management
    # ------------------------------------------

    st.divider()

    st.subheader(
        "Subject Management"
    )

    subject_tab1, subject_tab2 = st.tabs(
        [
            "Add Subject",
            "View Subjects"
        ]
    )

    # ------------------------------------------
    # Add Subject
    # ------------------------------------------

    with subject_tab1:

        departments = (
            db.query(Department)
            .order_by(Department.name)
            .all()
        )

        if not departments:

            st.warning(
                "Please create a department first."
            )

        else:

            department_options = {
                f"{department.code} - {department.name}":
                    department
                for department in departments
            }

            with st.form(
                "add_subject_form"
            ):

                subject_code = st.text_input(
                    "Subject Code",
                    placeholder="Example: CS401"
                )

                subject_name = st.text_input(
                    "Subject Name",
                    placeholder="Example: Python Programming"
                )

                selected_department = st.selectbox(
                    "Department",
                    list(
                        department_options.keys()
                    )
                )

                selected_department_obj = (
                    department_options[
                        selected_department
                    ]
                )

                submitted = st.form_submit_button(
                    "Add Subject"
                )

                if submitted:

                    subject_code = (
                        subject_code.strip().upper()
                    )

                    subject_name = (
                        subject_name.strip()
                    )

                    if not subject_code:

                        st.error(
                            "Subject code is required."
                        )

                    elif not subject_name:

                        st.error(
                            "Subject name is required."
                        )

                    else:

                        existing_code = (
                            db.query(Subject)
                            .filter(
                                Subject.code
                                == subject_code
                            )
                            .first()
                        )

                        existing_name = (
                            db.query(Subject)
                            .filter(
                                Subject.name
                                == subject_name,
                                Subject.department_id
                                == selected_department_obj.id
                            )
                            .first()
                        )

                        if existing_code:

                            st.error(
                                "Subject code already exists."
                            )

                        elif existing_name:

                            st.error(
                                "Subject with this name already "
                                "exists in the department."
                            )

                        else:

                            subject = Subject(
                                code=subject_code,
                                name=subject_name,
                                department_id=(
                                    selected_department_obj.id
                                )
                            )

                            db.add(subject)
                            db.commit()
                            db.refresh(subject)

                            st.success(
                                f"Subject '{subject.name}' "
                                "created successfully."
                            )

    # ------------------------------------------
    # View Subjects
    # ------------------------------------------

    with subject_tab2:

        subjects = (
            db.query(Subject)
            .order_by(Subject.code)
            .all()
        )

        if not subjects:

            st.info(
                "No subjects have been added yet."
            )

        else:

            st.write(
                f"Total Subjects: {len(subjects)}"
            )

            for subject in subjects:

                department = (
                    db.query(Department)
                    .filter(
                        Department.id
                        == subject.department_id
                    )
                    .first()
                )

                st.write(
                    f"**{subject.code}** — "
                    f"{subject.name}"
                )

                st.caption(
                    f"Department: "
                    f"{department.code if department else 'N/A'}"
                    f" - "
                    f"{department.name if department else 'N/A'}"
                )

    # ------------------------------------------
    # Faculty Assignment
    # ------------------------------------------

    st.divider()

    st.subheader(
        "Faculty Assignment"
    )

    assignment_tab1, assignment_tab2 = st.tabs(
        [
            "Assign Faculty",
            "View Assignments"
        ]
    )

    # ------------------------------------------
    # Assign Faculty
    # ------------------------------------------

    with assignment_tab1:

        faculty_members = (
            db.query(Faculty)
            .order_by(Faculty.name)
            .all()
        )

        subjects = (
            db.query(Subject)
            .order_by(Subject.code)
            .all()
        )

        sections = (
            db.query(Section)
            .order_by(Section.name)
            .all()
        )

        if not faculty_members:

            st.warning(
                "Please create a faculty member first."
            )

        elif not subjects:

            st.warning(
                "Please create a subject first."
            )

        elif not sections:

            st.warning(
                "Please create a section first."
            )

        else:

            faculty_options = {
                f"{faculty.employee_id} - {faculty.name}":
                    faculty
                for faculty in faculty_members
            }

            subject_options = {
                f"{subject.code} - {subject.name}":
                    subject
                for subject in subjects
            }

            section_options = {
                section.name:
                    section
                for section in sections
            }

            with st.form(
                "faculty_assignment_form"
            ):

                selected_faculty = st.selectbox(
                    "Faculty",
                    list(
                        faculty_options.keys()
                    )
                )

                selected_subject = st.selectbox(
                    "Subject",
                    list(
                        subject_options.keys()
                    )
                )

                selected_section = st.selectbox(
                    "Section",
                    list(
                        section_options.keys()
                    )
                )

                submitted = st.form_submit_button(
                    "Assign Faculty"
                )

                if submitted:

                    faculty_obj = (
                        faculty_options[
                            selected_faculty
                        ]
                    )

                    subject_obj = (
                        subject_options[
                            selected_subject
                        ]
                    )

                    section_obj = (
                        section_options[
                            selected_section
                        ]
                    )

                    existing_assignment = (
                        db.query(FacultySubject)
                        .filter(
                            FacultySubject.faculty_id
                            == faculty_obj.id,
                            FacultySubject.subject_id
                            == subject_obj.id,
                            FacultySubject.section_id
                            == section_obj.id
                        )
                        .first()
                    )

                    if existing_assignment:

                        st.error(
                            "This faculty is already assigned "
                            "to this subject and section."
                        )

                    else:

                        assignment = FacultySubject(
                            faculty_id=faculty_obj.id,
                            subject_id=subject_obj.id,
                            section_id=section_obj.id
                        )

                        db.add(assignment)
                        db.commit()
                        db.refresh(assignment)

                        st.success(
                            f"{faculty_obj.name} assigned to "
                            f"{subject_obj.code} - "
                            f"{subject_obj.name}, "
                            f"Section {section_obj.name}."
                        )

    # ------------------------------------------
    # View Assignments
    # ------------------------------------------

    with assignment_tab2:

        assignments = (
            db.query(FacultySubject)
            .order_by(FacultySubject.id)
            .all()
        )

        if not assignments:

            st.info(
                "No faculty assignments have been created yet."
            )

        else:

            st.write(
                f"Total Assignments: {len(assignments)}"
            )

            for assignment in assignments:

                faculty = (
                    db.query(Faculty)
                    .filter(
                        Faculty.id
                        == assignment.faculty_id
                    )
                    .first()
                )

                subject = (
                    db.query(Subject)
                    .filter(
                        Subject.id
                        == assignment.subject_id
                    )
                    .first()
                )

                section = (
                    db.query(Section)
                    .filter(
                        Section.id
                        == assignment.section_id
                    )
                    .first()
                )

                if faculty and subject and section:

                    st.write(
                        f"**{faculty.name}** → "
                        f"**{subject.code} - "
                        f"{subject.name}** → "
                        f"**Section {section.name}**"
                    )

    # Student Subject Enrollment
    st.header("Student Subject Enrollment")

    enroll_tab1, enroll_tab2 = st.tabs(
        ["Enroll Student", "View Enrollments"]
    )

    with enroll_tab1:
        students = (
            db.query(Student)
            .order_by(Student.roll_number)
            .all()
        )

        subjects = (
            db.query(Subject)
            .order_by(Subject.code)
            .all()
        )

        if not students:
            st.info("No students available. Add students first.")
        elif not subjects:
            st.info("No subjects available. Add subjects first.")
        else:
            student_options = {
                f"{student.roll_number} - {student.name}": student
                for student in students
            }

            subject_options = {
                f"{subject.code} - {subject.name}": subject
                for subject in subjects
            }

            selected_student_label = st.selectbox(
                "Student",
                list(student_options.keys())
            )

            selected_subject_label = st.selectbox(
                "Subject",
                list(subject_options.keys())
            )

            if st.button("Enroll Student"):
                selected_student = student_options[selected_student_label]
                selected_subject = subject_options[selected_subject_label]

                existing_enrollment = (
                    db.query(Enrollment)
                    .filter(
                        Enrollment.student_id == selected_student.id,
                        Enrollment.subject_id == selected_subject.id
                    )
                    .first()
                )

                if existing_enrollment:
                    st.warning(
                        "This student is already enrolled in this subject."
                    )
                else:
                    enrollment = Enrollment(
                        student_id=selected_student.id,
                        subject_id=selected_subject.id
                    )

                    db.add(enrollment)
                    db.commit()

                    st.success(
                        f"{selected_student.name} enrolled in "
                        f"{selected_subject.name} successfully."
                    )

    with enroll_tab2:
        enrollments = (
            db.query(Enrollment)
            .order_by(Enrollment.id)
            .all()
        )

        if not enrollments:
            st.info("No student subject enrollments found.")
        else:
            for enrollment in enrollments:
                student = db.query(Student).filter(
                    Student.id == enrollment.student_id
                ).first()

                subject = db.query(Subject).filter(
                    Subject.id == enrollment.subject_id
                ).first()

                if student and subject:
                    st.write(
                        f"**{student.roll_number} - {student.name}** "
                        f"→ **{subject.code} - {subject.name}**"
                    )
# ==================================================
# FACULTY DASHBOARD
# ==================================================

elif user["role"] == "FACULTY":

    # ------------------------------------------
    # Faculty Dashboard
    # ------------------------------------------

    st.header(
        "Faculty Dashboard"
    )

    faculty = (
        db.query(Faculty)
        .filter(
            Faculty.user_id == user["id"]
        )
        .first()
    )

    if not faculty:

        st.error(
            "Faculty profile not found."
        )

    else:

        st.write(
            f"Welcome, **{faculty.name}**"
        )

        st.divider()

        # ------------------------------------------
        # Get Faculty Assignments
        # ------------------------------------------

        assignments = (
            db.query(FacultySubject)
            .filter(
                FacultySubject.faculty_id
                == faculty.id
            )
            .all()
        )

        if not assignments:

            st.warning(
                "No subjects or sections have been "
                "assigned to you yet."
            )

        else:

            st.subheader(
                "Mark Attendance"
            )

            assignment_options = {}

            for assignment in assignments:

                subject = (
                    db.query(Subject)
                    .filter(
                        Subject.id
                        == assignment.subject_id
                    )
                    .first()
                )

                section = (
                    db.query(Section)
                    .filter(
                        Section.id
                        == assignment.section_id
                    )
                    .first()
                )

                if subject and section:

                    label = (
                        f"{subject.code} - "
                        f"{subject.name} | "
                        f"Section {section.name}"
                    )

                    assignment_options[
                        label
                    ] = assignment

            if not assignment_options:

                st.warning(
                    "No valid assignments found."
                )

            else:

                selected_assignment = st.selectbox(
                    "Subject & Section",
                    list(
                        assignment_options.keys()
                    )
                )

                selected_assignment_obj = (
                    assignment_options[
                        selected_assignment
                    ]
                )

                selected_date = st.date_input(
                    "Attendance Date"
                )

                selected_period = st.number_input(
                    "Period",
                    min_value=1,
                    max_value=12,
                    value=1,
                    step=1
                )

                if selected_date > date.today():

                    st.error(
                        "Attendance cannot be marked "
                        "for a future date."
                    )

                else:

                    subject_id = (
                        selected_assignment_obj.subject_id
                    )

                    section_id = (
                        selected_assignment_obj.section_id
                    )

                    session_datetime = datetime.combine(
                        selected_date,
                        datetime.min.time()
                    )

                    existing_session = (
                        db.query(ClassSession)
                        .filter(
                            ClassSession.subject_id
                            == subject_id,
                            ClassSession.section_id
                            == section_id,
                            ClassSession.session_date
                            == session_datetime,
                            ClassSession.period
                            == selected_period
                        )
                        .first()
                    )

                    if existing_session:

                        st.warning(
                            "Attendance session already "
                            "exists for this subject, "
                            "section, date and period."
                        )

                    else:

                        st.info(
                            "No attendance session exists "
                            "for this selection."
                        )

                        if st.button(
                            "Load Students",
                            type="primary"
                        ):

                            st.session_state[
                                "attendance_session_data"
                            ] = {
                                "subject_id":
                                    subject_id,
                                "section_id":
                                    section_id,
                                "faculty_id":
                                    faculty.id,
                                "session_date":
                                    selected_date,
                                "period":
                                    selected_period
                            }

                            st.rerun()

        # ------------------------------------------
        # Attendance Marking
        # ------------------------------------------

        if "attendance_session_data" in st.session_state:

            session_data = (
                st.session_state[
                    "attendance_session_data"
                ]
            )

            if (
                session_data["faculty_id"]
                != faculty.id
            ):

                st.error(
                    "Invalid attendance session."
                )

            else:

                st.divider()

                st.subheader(
                    "Student Attendance"
                )

                students = (
                    db.query(Student)
                    .join(
                        Enrollment,
                        Enrollment.student_id == Student.id
                    )
                    .filter(
                        Student.section_id
                        == session_data["section_id"],
                        Enrollment.subject_id
                        == session_data["subject_id"]
                    )
                    .order_by(
                        Student.roll_number
                    )
                    .all()
                )
                if not students:

                    st.warning(
                        "No students are enrolled "
                        "in this section."
                    )

                else:

                    st.write(
                        f"Total Students: {len(students)}"
                    )

                    attendance_statuses = {}

                    for student in students:

                        status = st.selectbox(
                            f"{student.roll_number} - "
                            f"{student.name}",
                            [
                                "PRESENT",
                                "ABSENT",
                                "LATE"
                            ],
                            key=(
                                f"attendance_"
                                f"{student.id}"
                            )
                        )

                        attendance_statuses[
                            student.id
                        ] = status

                    st.divider()

                    col1, col2 = st.columns(2)

                    with col1:

                        submit_attendance = st.button(
                            "Submit Attendance",
                            type="primary"
                        )

                    with col2:

                        cancel_attendance = st.button(
                            "Cancel"
                        )

                    if cancel_attendance:

                        del st.session_state[
                            "attendance_session_data"
                        ]

                        st.rerun()

                    if submit_attendance:

                        session_date = (
                            session_data[
                                "session_date"
                            ]
                        )

                        session_datetime = (
                            datetime.combine(
                                session_date,
                                datetime.min.time()
                            )
                        )

                        existing_session = (
                            db.query(ClassSession)
                            .filter(
                                ClassSession.subject_id
                                == session_data[
                                    "subject_id"
                                ],
                                ClassSession.section_id
                                == session_data[
                                    "section_id"
                                ],
                                ClassSession.session_date
                                == session_datetime,
                                ClassSession.period
                                == session_data[
                                    "period"
                                ]
                            )
                            .first()
                        )

                        if existing_session:

                            st.error(
                                "Attendance for this "
                                "subject, section, date "
                                "and period has already "
                                "been submitted."
                            )

                        else:

                            try:

                                class_session = ClassSession(
                                    subject_id=(
                                        session_data[
                                            "subject_id"
                                        ]
                                    ),
                                    section_id=(
                                        session_data[
                                            "section_id"
                                        ]
                                    ),
                                    faculty_id=faculty.id,
                                    session_date=(
                                        session_datetime
                                    ),
                                    period=(
                                        session_data[
                                            "period"
                                        ]
                                    )
                                )

                                db.add(
                                    class_session
                                )

                                db.flush()

                                for (
                                    student_id,
                                    status
                                ) in (
                                    attendance_statuses.items()
                                ):

                                    attendance = Attendance(
                                        session_id=(
                                            class_session.id
                                        ),
                                        student_id=(
                                            student_id
                                        ),
                                        status=status
                                    )

                                    db.add(
                                        attendance
                                    )

                                audit_log = AuditLog(
                                    user_id=user["id"],
                                    action="MARK_ATTENDANCE",
                                    entity_type="CLASS_SESSION",
                                    entity_id=(
                                        class_session.id
                                    ),
                                    details=(
                                        f"Attendance marked "
                                        f"for {len(students)} "
                                        f"students."
                                    )
                                )

                                db.add(
                                    audit_log
                                )

                                db.commit()

                                del st.session_state[
                                    "attendance_session_data"
                                ]

                                st.success(
                                    "Attendance submitted "
                                    "successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                db.rollback()

                                st.error(
                                    "Unable to save attendance."
                                )

                                st.exception(e)
        # ==================================================
        # FACULTY DASHBOARD: REQUEST ATTENDANCE CORRECTION
        # ==================================================

        if user["role"] == "FACULTY":

            st.title("👨‍🏫 Faculty Dashboard")

            # (Keep your existing Faculty Dashboard sections like Mark Attendance, History, etc. here)

            st.divider()
            st.subheader("Request Attendance Correction")

            # Fetch faculty record linked to the logged-in user
            faculty_obj = db.query(Faculty).filter(Faculty.user_id == user["id"]).first()

            if not faculty_obj:
                st.warning("Faculty profile not found for this user account.")
            else:
                # Get attendance records for sessions taught by this faculty member
                sessions_taught = (
                    db.query(ClassSession)
                    .join(FacultySubject, ClassSession.subject_id == FacultySubject.subject_id)
                    .filter(FacultySubject.faculty_id == faculty_obj.id)
                    .all()
                )
                session_ids = [s.id for s in sessions_taught]

                if not session_ids:
                    st.info("No class sessions found to request corrections for.")
                else:
                    recent_attendance = (
                        db.query(Attendance)
                        .filter(Attendance.session_id.in_(session_ids))
                        .order_by(Attendance.id.desc())
                        .limit(50)
                        .all()
                    )

                    if not recent_attendance:
                        st.info("No attendance records found.")
                    else:
                        attendance_options = {}
                        for att in recent_attendance:
                            stud = db.query(Student).filter(Student.id == att.student_id).first()
                            sess = db.query(ClassSession).filter(ClassSession.id == att.session_id).first()
                            subj = db.query(Subject).filter(Subject.id == sess.subject_id).first() if sess else None

                            label = (
                                f"{stud.name if stud else 'Unknown'} "
                                f"({stud.roll_number if stud else 'Unknown'}) | "
                                f"Subject: {subj.code if subj else 'Unknown'} | "
                                f"Date: {sess.session_date.date() if sess else 'N/A'} | "
                                f"Current: {att.status}"
                            )
                            attendance_options[label] = att

                        with st.form("request_correction_form"):
                            selected_attendance_label = st.selectbox(
                                "Select Attendance Record to Correct",
                                list(attendance_options.keys())
                            )

                            selected_att_obj = attendance_options[selected_attendance_label]

                            new_status = st.selectbox(
                                "Proposed New Status",
                                ["PRESENT", "ABSENT", "LATE"]
                            )

                            reason = st.text_area(
                                "Reason for Correction",
                                placeholder="Example: Student arrived late but was marked absent by mistake."
                            )

                            submitted = st.form_submit_button("Submit Correction Request")

                            if submitted:
                                if not reason.strip():
                                    st.error("Please provide a reason for the correction.")
                                elif new_status == selected_att_obj.status:
                                    st.error("The proposed status is the same as the current status.")
                                else:
                                    success, message = request_correction(
                                        db=db,
                                        attendance_id=selected_att_obj.id,
                                        requested_by=faculty_obj.id,
                                        new_status=new_status,
                                        reason=reason.strip()
                                    )

                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
        # ------------------------------------------
        # Attendance History
        # ------------------------------------------

        st.divider()

        st.subheader(
            "Attendance History"
        )

        faculty_sessions = (
            db.query(ClassSession)
            .filter(
                ClassSession.faculty_id
                == faculty.id
            )
            .order_by(
                ClassSession.session_date.desc(),
                ClassSession.period.desc()
            )
            .all()
        )

        if not faculty_sessions:

            st.info(
                "No attendance history available."
            )

        else:

            for attendance_session in faculty_sessions:

                subject = (
                    db.query(Subject)
                    .filter(
                        Subject.id
                        == attendance_session.subject_id
                    )
                    .first()
                )

                section = (
                    db.query(Section)
                    .filter(
                        Section.id
                        == attendance_session.section_id
                    )
                    .first()
                )

                attendance_records = (
                    db.query(Attendance)
                    .filter(
                        Attendance.session_id
                        == attendance_session.id
                    )
                    .all()
                )

                present_count = sum(
                    1
                    for record in attendance_records
                    if record.status == "PRESENT"
                )

                late_count = sum(
                    1
                    for record in attendance_records
                    if record.status == "LATE"
                )

                absent_count = sum(
                    1
                    for record in attendance_records
                    if record.status == "ABSENT"
                )

                total_count = len(
                    attendance_records
                )

                if subject and section:
                    st.write(
                        f"**{subject.code} - "
                        f"{subject.name}** | "
                        f"Section {section.name} | "
                        f"Date: "
                        f"{attendance_session.session_date.date()} | "
                        f"Period: "
                        f"{attendance_session.period}"
                    )

                    st.write(
                        f"Total: {total_count} | "
                        f"Present: {present_count} | "
                        f"Late: {late_count} | "
                        f"Absent: {absent_count}"
                    )

                    st.divider()
        # ==================================================
        # ATTENDANCE CORRECTION REQUEST
        # ==================================================

        st.divider()
        st.subheader("Attendance Correction")

        attendance_records = (
            db.query(Attendance)
            .join(
                ClassSession,
                ClassSession.id == Attendance.session_id
            )
            .filter(
                ClassSession.faculty_id == faculty.id
            )
            .order_by(
                ClassSession.session_date.desc(),
                ClassSession.period.desc()
            )
            .all()
        )

        if not attendance_records:
            st.info(
                "No attendance records are available "
                "for correction."
            )
        else:

            correction_options = []

            for record in attendance_records:

                session = (
                    db.query(ClassSession)
                    .filter(
                        ClassSession.id == record.session_id
                    )
                    .first()
                )

                student = (
                    db.query(Student)
                    .filter(
                        Student.id == record.student_id
                    )
                    .first()
                )

                subject = (
                    db.query(Subject)
                    .filter(
                        Subject.id == session.subject_id
                    )
                    .first()
                ) if session else None

                if session and student and subject:

                    label = (
                        f"{student.roll_number} - "
                        f"{student.name} | "
                        f"{subject.code} | "
                        f"{session.session_date.date()} | "
                        f"Period {session.period} | "
                        f"{record.status}"
                    )

                    correction_options.append(
                        (label, record.id)
                    )

            if correction_options:

                selected_label = st.selectbox(
                    "Select attendance record",
                    [
                        option[0]
                        for option in correction_options
                    ]
                )

                selected_attendance_id = next(
                    option[1]
                    for option in correction_options
                    if option[0] == selected_label
                )

                selected_record = (
                    db.query(Attendance)
                    .filter(
                        Attendance.id
                        == selected_attendance_id
                    )
                    .first()
                )

                if selected_record:

                    st.write(
                        f"Current Status: "
                        f"**{selected_record.status}**"
                    )

                    new_status = st.selectbox(
                        "New Status",
                        [
                            "PRESENT",
                            "ABSENT",
                            "LATE"
                        ]
                    )

                    reason = st.text_area(
                        "Reason for correction",
                        placeholder=(
                            "Example: Student was marked "
                            "absent by mistake."
                        )
                    )

                    if st.button(
                        "Submit Correction Request"
                    ):

                        success, message = request_correction(
                            db=db,
                            attendance_id=selected_attendance_id,
                            faculty_id=faculty.id,
                            new_status=new_status,
                            reason=reason,
                            user_id=user.id,
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        # ------------------------------------------
        # Attendance Summary
        # ------------------------------------------

        st.divider()

        st.subheader(
            "Attendance Summary"
        )

        for assignment in assignments:

            subject = (
                db.query(Subject)
                .filter(
                    Subject.id
                    == assignment.subject_id
                )
                .first()
            )

            section = (
                db.query(Section)
                .filter(
                    Section.id
                    == assignment.section_id
                )
                .first()
            )

            if not subject or not section:
                continue

            st.markdown(
                f"### {subject.code} - "
                f"{subject.name} | "
                f"Section {section.name}"
            )

            enrolled_students = (
                db.query(Student)
                .join(
                    Enrollment,
                    Enrollment.student_id
                    == Student.id
                )
                .filter(
                    Student.section_id
                    == section.id,
                    Enrollment.subject_id
                    == subject.id
                )
                .order_by(
                    Student.roll_number
                )
                .all()
            )

            if not enrolled_students:

                st.info(
                    "No students are enrolled "
                    "in this subject."
                )

            else:

                for student in enrolled_students:

                    attendance_records = (
                        db.query(Attendance)
                        .join(
                            ClassSession,
                            ClassSession.id
                            == Attendance.session_id
                        )
                        .filter(
                            Attendance.student_id
                            == student.id,
                            ClassSession.subject_id
                            == subject.id,
                            ClassSession.section_id
                            == section.id
                        )
                        .all()
                    )

                    total_classes = len(
                        attendance_records
                    )

                    present_count = sum(
                        1
                        for record
                        in attendance_records
                        if record.status
                        == "PRESENT"
                    )

                    late_count = sum(
                        1
                        for record
                        in attendance_records
                        if record.status
                        == "LATE"
                    )

                    absent_count = sum(
                        1
                        for record
                        in attendance_records
                        if record.status
                        == "ABSENT"
                    )

                    attended_classes = (
                            present_count
                            + late_count
                    )

                    if total_classes > 0:

                        attendance_percentage = (
                                                        attended_classes
                                                        / total_classes
                                                ) * 100

                    else:

                        attendance_percentage = 0

                    if attendance_percentage >= 75:

                        attendance_status = (
                            "SAFE"
                        )

                    elif attendance_percentage >= 65:

                        attendance_status = (
                            "WARNING"
                        )

                    else:

                        attendance_status = (
                            "LOW"
                        )

                    st.write(
                        f"**{student.roll_number} - "
                        f"{student.name}**"
                    )

                    st.write(
                        f"Total: {total_classes} | "
                        f"Present: {present_count} | "
                        f"Late: {late_count} | "
                        f"Absent: {absent_count} | "
                        f"Attendance: "
                        f"{attendance_percentage:.2f}% | "
                        f"Status: "
                        f"**{attendance_status}**"
                    )

            st.divider()
# ==================================================
# STUDENT DASHBOARD
# ==================================================

elif user["role"] == "STUDENT":

    # ------------------------------------------
    # Student Dashboard
    # ------------------------------------------

    st.header(
        "Student Dashboard"
    )

    student = (
        db.query(Student)
        .filter(
            Student.user_id == user["id"]
        )
        .first()
    )

    if not student:

        st.error(
            "Student profile not found."
        )

    else:

        st.write(
            f"Welcome, **{student.name}**"
        )

        st.write(
            f"Roll Number: **{student.roll_number}**"
        )

        st.divider()

        # ------------------------------------------
        # Get Enrolled Subjects
        # ------------------------------------------

        enrollments = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id
                == student.id
            )
            .all()
        )

        if not enrollments:

            st.info(
                "You are not enrolled in any subjects yet."
            )

        else:

            st.subheader(
                "My Attendance"
            )

            for enrollment in enrollments:

                subject = (
                    db.query(Subject)
                    .filter(
                        Subject.id
                        == enrollment.subject_id
                    )
                    .first()
                )

                if not subject:
                    continue

                attendance_records = (
                    db.query(Attendance)
                    .join(
                        ClassSession,
                        ClassSession.id
                        == Attendance.session_id
                    )
                    .filter(
                        Attendance.student_id
                        == student.id,
                        ClassSession.subject_id
                        == subject.id
                    )
                    .order_by(
                        ClassSession.session_date.desc(),
                        ClassSession.period.desc()
                    )
                    .all()
                )

                total_classes = len(
                    attendance_records
                )

                present_count = sum(
                    1
                    for record
                    in attendance_records
                    if record.status == "PRESENT"
                )

                late_count = sum(
                    1
                    for record
                    in attendance_records
                    if record.status == "LATE"
                )

                absent_count = sum(
                    1
                    for record
                    in attendance_records
                    if record.status == "ABSENT"
                )

                attended_classes = (
                    present_count
                    + late_count
                )

                if total_classes > 0:

                    attendance_percentage = (
                        attended_classes
                        / total_classes
                    ) * 100

                else:

                    attendance_percentage = 0

                if attendance_percentage >= 75:

                    attendance_status = "SAFE"

                elif attendance_percentage >= 65:

                    attendance_status = "WARNING"

                else:

                    attendance_status = "LOW"

                st.markdown(
                    f"### {subject.code} - "
                    f"{subject.name}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "Total Classes",
                        total_classes
                    )

                with col2:

                    st.metric(
                        "Present",
                        present_count
                    )

                with col3:

                    st.metric(
                        "Late",
                        late_count
                    )

                with col4:

                    st.metric(
                        "Absent",
                        absent_count
                    )

                st.write(
                    f"**Attendance: "
                    f"{attendance_percentage:.2f}%**"
                )

                st.write(
                    f"Status: **{attendance_status}**"
                )

                if attendance_percentage < 75:

                    st.warning(
                        "Your attendance is below "
                        "the required 75% threshold."
                    )

                else:

                    st.success(
                        "Your attendance is currently "
                        "above the 75% threshold."
                    )

                st.divider()

        # ------------------------------------------
        # Attendance History
        # ------------------------------------------

        st.subheader(
            "Attendance History"
        )

        student_attendance = (
            db.query(Attendance)
            .join(
                ClassSession,
                ClassSession.id
                == Attendance.session_id
            )
            .join(
                Subject,
                Subject.id
                == ClassSession.subject_id
            )
            .filter(
                Attendance.student_id
                == student.id
            )
            .order_by(
                ClassSession.session_date.desc(),
                ClassSession.period.desc()
            )
            .all()
        )

        if not student_attendance:

            st.info(
                "No attendance records available."
            )

        else:

            for record in student_attendance:

                session = (
                    db.query(ClassSession)
                    .filter(
                        ClassSession.id
                        == record.session_id
                    )
                    .first()
                )

                subject = (
                    db.query(Subject)
                    .filter(
                        Subject.id
                        == session.subject_id
                    )
                    .first()
                )

                if session and subject:

                    st.write(
                        f"**{subject.code} - "
                        f"{subject.name}** | "
                        f"Date: "
                        f"{session.session_date.date()} | "
                        f"Period: "
                        f"{session.period} | "
                        f"Status: **{record.status}**"
                    )
    # ==================================================
    # STUDENT DASHBOARD
    # ==================================================

    # elif user["role"] == "STUDENT":
    #
    # st.title("Student Dashboard")
    #
    # student = (
    #     db.query(Student)
    #     .filter(Student.user_id == user["id"])
    #     .first()
    # )
    #
    # if not student:
    #     st.error("Student profile not found.")
    # else:
    #     st.write(f"Welcome, **{student.name}** ({student.roll_number})")
    #     st.divider()
    #
    #     st.subheader("My Attendance Summary & History")
    #
    #     # Get enrolled subjects or subjects for student's section
    #     subjects = (
    #         db.query(Subject)
    #         .filter(Subject.department_id == student.department_id)
    #         .all()
    #     )
    #
    #     if not subjects:
    #         st.info("No subjects found.")
    #     else:
    #         for sub in subjects:
    #             # Get all sessions for this subject & student's section
    #             sessions = (
    #                 db.query(ClassSession)
    #                 .filter(
    #                     ClassSession.subject_id == sub.id,
    #                     ClassSession.section_id == student.section_id
    #                 )
    #                 .all()
    #             )
    #             session_ids = [s.id for s in sessions]
    #
    #             if not session_ids:
    #                 continue
    #
    #             attendance_records = (
    #                 db.query(Attendance)
    #                 .filter(
    #                     Attendance.student_id == student.id,
    #                     Attendance.session_id.in_(session_ids)
    #                 )
    #                 .all()
    #             )
    #
    #             total_classes = len(attendance_records)
    #             present_classes = sum(
    #                 1 for a in attendance_records if a.status == "PRESENT"
    #             )
    #
    #             percentage = (
    #                 (present_classes / total_classes) * 100
    #                 if total_classes > 0
    #                 else 100.0
    #             )
    #
    #             st.markdown(f"### 📚 {sub.code} — {sub.name}")
    #
    #             if total_classes > 0:
    #                 st.write(f"Attendance: **{present_classes}/{total_classes} classes ({percentage:.1f}%)**")
    #                 if percentage < 75.0:
    #                     st.warning("⚠️ Low attendance warning: Below 75% threshold!")
    #             else:
    #                 st.write("Attendance: No classes recorded yet.")
    #
    #             # Show detailed breakdown with correction status if any
    #             with st.expander("View Session Details"):
    #                 for att in attendance_records:
    #                     sess = db.query(ClassSession).filter(ClassSession.id == att.session_id).first()
    #                     correction = (
    #                         db.query(AttendanceCorrection)
    #                         .filter(AttendanceCorrection.attendance_id == att.id)
    #                         .first()
    #                     )
    #
    #                     status_text = f"Status: **{att.status}**"
    #                     if correction:
    #                         status_text += f" (Correction: {correction.status})"
    #
    #                     st.write(
    #                         f"- Date: {sess.session_date.date() if sess else 'N/A'} | "
    #                         f"Period: {sess.period if sess else 'N/A'} | {status_text}"
    #                     )
    #             st.divider()
# ==================================================
# INVALID ROLE
# ==================================================

else:

    st.error(
        "Invalid user role."
    )


# --------------------------------------------------
# Close database session
# --------------------------------------------------

db.close()

