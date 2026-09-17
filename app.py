import streamlit as st
import pandas as pd
import os

def check_password():
    """Returns True if the user entered the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Student Access Portal")
    st.write("Please enter the class password to access the app.")

    user_password = st.text_input("Enter Password", type="password")

    if st.button("Log In"):
        if user_password == st.secrets.get("APP_PASSWORD", "default_pass"):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect password. Please try again.")

    return False

# Protect the main app content
if not check_password():
    st.stop()
    
# --- CONFIGURATION ---
DATA_FILE = "student_tracker.csv"
UPLOAD_DIR = "uploads"
INSTRUCTOR_PASSWORD = "tye6632"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_data():
    required_columns = [
        "Group_ID", "Student_Name", "Student_ID", 
        "Part_A_Company", "Part_A_Industry", "Part_A_File", "Part_A_Marks", "Part_A_Feedback",
        "Part_B_File", "Part_B_Marks", "Part_B_Feedback",
        "Part_C_File", "Part_C_Marks", "Part_C_Feedback",
        "Appendix_File"
    ]
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        for col in required_columns:
            if col not in df.columns:
                if "Marks" in col:
                    df[col] = 0.0
                else:
                    df[col] = ""
        df = df[required_columns]
        df.to_csv(DATA_FILE, index=False)
        return df
    else:
        df = pd.DataFrame(columns=required_columns)
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def save_uploaded_file(uploaded_file, group_id, student_id, part_label):
    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1]
        clean_group = str(group_id).replace(" ", "_")
        filename = f"{clean_group}_{student_id}_{part_label}{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath
    return ""

# Page Config
st.set_page_config(page_title="Multi-Group Assignment Tracker", layout="wide")
df = load_data()

# Sidebar Navigation
st.sidebar.title("⚙️ Navigation")
user_role = st.sidebar.radio("Mode:", ["Student Portal", "Instructor Dashboard"])

# ==========================================
# 1. STUDENT PORTAL (Public Access)
# ==========================================
if user_role == "Student Portal":
    st.title("🎓 Student Submission & Registration Portal")
    
    # --- YOUR NEW SNIPPET STARTS HERE ---
    st.subheader("Step 1: Student Identification & Company Selection")

    c1, c2 = st.columns(2)
    with c1:
        group_num = st.number_input("Enter Your Group Number:", min_value=1, max_value=100, value=1)
        group_id = f"Group {group_num}"
        student_id = st.text_input("Enter Student ID:").strip()

    with c2:
        student_name = st.text_input("Enter Full Name:").strip()
        
        # Check if student already exists in database
        existing_record = df[df["Student_ID"] == student_id] if (not df.empty and student_id) else pd.DataFrame()
        
        current_company = ""
        if not existing_record.empty:
            current_company = existing_record.iloc[0]["Part_A_Company"]
            st.info(f"ℹ️ Currently registered company: **{current_company}**")

        # Input for new or updated company
        company_name = st.text_input(
            "Company Name (Type a new name to change your selection):", 
            value=current_company
        ).strip()
        
        industry_name = st.text_input("Company Industry:").strip()

    # --- DUPLICATE COMPANY CHECK ---
    if company_name and not df.empty:
        # Look for duplicates excluding the CURRENT student's own record
        other_students_df = df[df["Student_ID"] != student_id]
        taken_companies = other_students_df["Part_A_Company"].dropna().str.strip().str.lower().tolist()
        
        if company_name.lower() in taken_companies:
            st.error(f"❌ **Company Unavailable:** '{company_name}' is already taken by another student!")
        elif current_company and company_name.lower() != current_company.lower():
            st.success(f"🔄 You are changing your company from **{current_company}** to **{company_name}**.")
    # --- YOUR NEW SNIPPET ENDS HERE ---

    st.markdown("---")
    st.subheader("Step 2: Assignment Document Uploads")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Part A (Individual Bloomberg Data & Analysis)")
        file_a = st.file_uploader("Upload Part A Document (Individual):", key="file_a")
        
        st.markdown("#### Part B (Group Discussion Report)")
        file_b = st.file_uploader("Upload Part B Group Report (1 member uploads for group):", key="file_b")

    with col_b:
        st.markdown("#### Part C (Individual Summary)")
        file_c = st.file_uploader("Upload Part C Document (Individual):", key="file_c")

        st.markdown("#### References & Appendix (Group Level)")
        file_app = st.file_uploader("Upload Reference List / Appendix (1 member uploads for group):", key="file_app")

    if st.button("🚀 Submit Assignment Files", type="primary"):
        if not student_id or not student_name or not company_name:
            st.warning("Please fill in Student ID, Name, and Company Name before submitting.")
        else:
            match_idx = df[df["Student_ID"] == student_id].index
            idx = match_idx[0] if len(match_idx) > 0 else len(df)
            
            path_a = save_uploaded_file(file_a, group_id, student_id, "PartA") if file_a else (df.loc[idx, "Part_A_File"] if idx in df.index and pd.notna(df.loc[idx, "Part_A_File"]) else "")
            path_b = save_uploaded_file(file_b, group_id, "GROUP", "PartB") if file_b else (df.loc[idx, "Part_B_File"] if idx in df.index and pd.notna(df.loc[idx, "Part_B_File"]) else "")
            path_c = save_uploaded_file(file_c, group_id, student_id, "PartC") if file_c else (df.loc[idx, "Part_C_File"] if idx in df.index and pd.notna(df.loc[idx, "Part_C_File"]) else "")
            path_app = save_uploaded_file(file_app, group_id, "GROUP", "Appendix") if file_app else (df.loc[idx, "Appendix_File"] if idx in df.index and pd.notna(df.loc[idx, "Appendix_File"]) else "")

            df.loc[idx, "Group_ID"] = group_id
            df.loc[idx, "Student_Name"] = student_name
            df.loc[idx, "Student_ID"] = student_id
            df.loc[idx, "Part_A_Company"] = company_name
            df.loc[idx, "Part_A_Industry"] = industry_name
            df.loc[idx, "Part_A_File"] = path_a
            df.loc[idx, "Part_C_File"] = path_c
            
            for col in ["Part_A_Marks", "Part_B_Marks", "Part_C_Marks"]:
                if idx not in df.index or pd.isna(df.loc[idx, col]):
                    df.loc[idx, col] = 0.0

            if path_b:
                group_indices = df[df["Group_ID"] == group_id].index
                for g_idx in group_indices:
                    df.loc[g_idx, "Part_B_File"] = path_b
            else:
                df.loc[idx, "Part_B_File"] = path_b

            if path_app:
                group_indices = df[df["Group_ID"] == group_id].index
                for g_idx in group_indices:
                    df.loc[g_idx, "Appendix_File"] = path_app
            else:
                df.loc[idx, "Appendix_File"] = path_app

            save_data(df)
            st.success("Submissions recorded successfully!")

# ==========================================
# 2. INSTRUCTOR DASHBOARD (Password Protected)
# ==========================================
else:
    st.title("🔒 Instructor Access Portal")
    
    pwd_input = st.text_input("Enter Instructor Password to Unlock Dashboard:", type="password")
    
    if pwd_input == INSTRUCTOR_PASSWORD:
        st.success("🔓 Password Verified! Welcome, Instructor.")
        st.markdown("---")
        
        st.header("🚨 System Compliance & Flags Notification Center")

        flags = []

        valid_companies = df["Part_A_Company"].dropna().str.strip().str.lower()
        company_counts = valid_companies[valid_companies != ""].value_counts()
        duplicates = company_counts[company_counts > 1].index.tolist()
        for dup in duplicates:
            dup_students = df[df["Part_A_Company"].str.strip().str.lower() == dup]
            s_list = ", ".join([f"{r['Student_Name']} ({r['Group_ID']})" for _, r in dup_students.iterrows()])
            flags.append(f"🚩 **DUPLICATE COMPANY ALERT:** '{dup.title()}' selected by multiple students: {s_list}")

        for _, row in df.iterrows():
            missing_parts = []
            if not str(row["Part_A_File"]).strip() or pd.isna(row["Part_A_File"]): missing_parts.append("Part A")
            if not str(row["Part_C_File"]).strip() or pd.isna(row["Part_C_File"]): missing_parts.append("Part C")
            
            if missing_parts:
                flags.append(f"⚠️ **MISSING INDIVIDUAL FILE ALERT:** {row['Student_Name']} ({row['Student_ID']}, {row['Group_ID']}) missing: {', '.join(missing_parts)}")

        for g_id, g_data in df.groupby("Group_ID"):
            first_row = g_data.iloc[0]
            missing_group_files = []
            if not str(first_row["Part_B_File"]).strip() or pd.isna(first_row["Part_B_File"]): missing_group_files.append("Part B Report")
            if not str(first_row["Appendix_File"]).strip() or pd.isna(first_row["Appendix_File"]): missing_group_files.append("Reference List / Appendix")
            
            if missing_group_files:
                flags.append(f"⚠️ **MISSING GROUP FILE ALERT:** {g_id} has not uploaded: {', '.join(missing_group_files)}")

            u_inds = g_data["Part_A_Industry"].nunique()
            if len(g_data) >= 3 and u_inds != 2:
                flags.append(f"⚠️ **GROUP INDUSTRY RULE ALERT:** {g_id} has {u_inds} unique industries selected (Exactly 2 required).")

        if flags:
            for flag in flags:
                st.warning(flag)
        else:
            st.success("✅ No compliance flags detected across all groups!")

        st.markdown("---")

        st.header("📋 Group Grading & Submission Management")
        
        all_groups = sorted(df["Group_ID"].unique()) if len(df) > 0 else ["Group 1"]
        selected_group = st.selectbox("Select Group to Grade:", all_groups)
        
        group_df = df[df["Group_ID"] == selected_group]

        if len(group_df) > 0:
            first_member = group_df.iloc[0]
            st.info(f"📁 **Group-Level Submissions for {selected_group}:**\n"
                    f"- **Part B Group Report:** {first_member['Part_B_File'] if str(first_member['Part_B_File']).strip() and pd.notna(first_member['Part_B_File']) else '❌ Missing'}\n"
                    f"- **Reference List / Appendix:** {first_member['Appendix_File'] if str(first_member['Appendix_File']).strip() and pd.notna(first_member['Appendix_File']) else '❌ Missing'}")

        for idx, row in group_df.iterrows():
            with st.expander(f"👤 {row['Student_Name']} ({row['Student_ID']}) - Company: {row['Part_A_Company']}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write("**Part A File (Individual):**", row["Part_A_File"] if str(row["Part_A_File"]).strip() and pd.notna(row["Part_A_File"]) else "❌ Missing")
                    marks_a = st.number_input(f"Part A Marks ({row['Student_ID']}):", 0.0, 100.0, float(row["Part_A_Marks"]))
                    fb_a = st.text_area(f"Part A Feedback ({row['Student_ID']}):", str(row["Part_A_Feedback"]) if pd.notna(row["Part_A_Feedback"]) else "")
                
                with c2:
                    st.write("**Part B File (Group):**", row["Part_B_File"] if str(row["Part_B_File"]).strip() and pd.notna(row["Part_B_File"]) else "❌ Missing")
                    marks_b = st.number_input(f"Part B Marks ({row['Student_ID']}):", 0.0, 100.0, float(row["Part_B_Marks"]))
                    fb_b = st.text_area(f"Part B Feedback ({row['Student_ID']}):", str(row["Part_B_Feedback"]) if pd.notna(row["Part_B_Feedback"]) else "")

                with c3:
                    st.write("**Part C File (Individual):**", row["Part_C_File"] if str(row["Part_C_File"]).strip() and pd.notna(row["Part_C_File"]) else "❌ Missing")
                    marks_c = st.number_input(f"Part C Marks ({row['Student_ID']}):", 0.0, 100.0, float(row["Part_C_Marks"]))
                    fb_c = st.text_area(f"Part C Feedback ({row['Student_ID']}):", str(row["Part_C_Feedback"]) if pd.notna(row["Part_C_Feedback"]) else "")

                df.loc[idx, "Part_A_Marks"] = marks_a
                df.loc[idx, "Part_A_Feedback"] = fb_a
                df.loc[idx, "Part_B_Marks"] = marks_b
                df.loc[idx, "Part_B_Feedback"] = fb_b
                df.loc[idx, "Part_C_Marks"] = marks_c
                df.loc[idx, "Part_C_Feedback"] = fb_c

        if st.button("💾 Save Grade Updates", type="primary"):
            save_data(df)
            st.success("Grades and feedback saved successfully!")
            
    elif pwd_input != "":
        st.error("❌ Incorrect Password. Access Denied.")
    else:
        st.info(" Please enter the instructor password above to view student marks, compliance reports, and grading controls.")
