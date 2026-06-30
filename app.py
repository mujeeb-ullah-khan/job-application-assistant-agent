import streamlit as st
from google import genai
import json
import os
from datetime import date

# ---------- Page setup ----------
st.set_page_config(page_title="Job Application Assistant Agent", page_icon="💼", layout="centered")

st.markdown("""
<style>
.main-header {
    padding: 1.8rem 2rem;
    background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%);
    border-radius: 14px;
    margin-bottom: 1.5rem;
}
.main-header h1 {
    color: white;
    font-size: 1.9rem;
    margin: 0;
}
.main-header p {
    color: #DBEAFE;
    margin: 0.3rem 0 0 0;
    font-size: 0.95rem;
}
div[data-testid="stTextArea"] textarea {
    border-radius: 10px;
}
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
}
div[data-testid="stExpander"] {
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}
</style>

<div class="main-header">
    <h1>💼 Job/Internship Application Assistant Agent</h1>
    <p>An AI agent that tailors cover letters and tracks your applications — built for Kaggle's AI Agents Intensive Vibe Coding Capstone</p>
</div>
""", unsafe_allow_html=True)

# ---------- Connect to Gemini ----------
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# ---------- Storage functions ----------
TRACKER_FILE = "applications.json"

def load_applications():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    return []

def save_applications(applications):
    with open(TRACKER_FILE, "w") as f:
        json.dump(applications, f, indent=2)

def log_application(company, role, status="Applied", notes=""):
    applications = load_applications()
    applications.append({
        "company": company,
        "role": role,
        "date_applied": str(date.today()),
        "status": status,
        "notes": notes
    })
    save_applications(applications)

def update_application_status(company, role, new_status):
    applications = load_applications()
    for app in applications:
        if app['company'].lower() == company.lower() and app['role'].lower() == role.lower():
            app['status'] = new_status
    save_applications(applications)

# ---------- Cover letter generator ----------
def generate_application_materials(resume_text, job_posting_text):
    prompt = f"""
You are a career assistant agent. You will be given a candidate's resume and a job posting.

Your tasks:
1. Write a tailored, professional cover letter (3-4 paragraphs) that connects the candidate's
   real skills/experience to this specific job posting. Do not invent skills or experience
   that aren't in the resume.
2. After the cover letter, add a section titled "SKILL MATCH" that lists:
   - Matched Skills: skills/experience from the resume that align with the job requirements
   - Gaps: requirements in the job posting that the resume doesn't clearly show

RESUME:
{resume_text}

JOB POSTING:
{job_posting_text}

Format your response with clear headers: "COVER LETTER" and "SKILL MATCH".
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# ---------- UI: Tabs ----------
# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 👤 About")
    st.write("Built by **Mujeeb Ullah Khan**")
    st.write("Information Systems student, UIN Raden Intan Lampung")
    st.markdown("---")
    st.markdown("### 🛠 Built With")
    st.write("- Google Gemini API")
    st.write("- Function calling / tool use")
    st.write("- Streamlit")
    st.markdown("---")
    st.markdown("### 🔗 Links")
    st.write("[GitHub Repo](https://github.com/mujeeb-ullah-khan/job-application-assistant-agent)")
    st.markdown("---")
    st.caption("Built for Kaggle's AI Agents Intensive Vibe Coding Capstone 🚀")
tab1, tab2 = st.tabs(["✍️ Generate Cover Letter", "📋 Application Tracker"])

# --- Tab 1: Cover letter generator ---
with tab1:
    st.subheader("Paste your resume and a job posting")
    resume_text = st.text_area("Resume", height=200, placeholder="Paste your resume here...")
    job_posting_text = st.text_area("Job Posting", height=200, placeholder="Paste the job posting here...")

    if st.button("Generate Cover Letter"):
        if resume_text.strip() and job_posting_text.strip():
            with st.spinner("Generating..."):
                result = generate_application_materials(resume_text, job_posting_text)
            st.markdown(result)
        else:
            st.warning("Please fill in both the resume and job posting.")

    st.divider()
    st.subheader("Log this application")
    col1, col2 = st.columns(2)
    with col1:
        company_input = st.text_input("Company name")
    with col2:
        role_input = st.text_input("Role")
    notes_input = st.text_input("Notes (optional)")

    if st.button("Log Application"):
        if company_input and role_input:
            log_application(company_input, role_input, notes=notes_input)
            st.success(f"Logged: {role_input} at {company_input}")
        else:
            st.warning("Please enter at least company and role.")

# --- Tab 2: Application tracker ---
with tab2:
    st.subheader("Your Applications")
    applications = load_applications()

    if not applications:
        st.info("No applications logged yet.")
    else:
        for i, app in enumerate(applications):
            with st.expander(f"{app['role']} at {app['company']} — {app['status']}"):
                st.write(f"**Date applied:** {app['date_applied']}")
                st.write(f"**Notes:** {app['notes'] if app['notes'] else 'None'}")
                new_status = st.selectbox(
                    "Update status",
                    ["Applied", "Interview Scheduled", "Offer", "Rejected"],
                    index=["Applied", "Interview Scheduled", "Offer", "Rejected"].index(app['status']) if app['status'] in ["Applied", "Interview Scheduled", "Offer", "Rejected"] else 0,
                    key=f"status_{i}"
                )
                if st.button("Update", key=f"update_{i}"):
                    update_application_status(app['company'], app['role'], new_status)
                    st.success("Updated! Refresh to see changes.")
