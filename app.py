import streamlit as st
from google import genai
import json
import PyPDF2
import io
import os
import pandas as pd
from datetime import date

# ---------- Page setup ----------
st.set_page_config(page_title="Job Application Assistant Agent", page_icon="💼", layout="wide")

st.markdown("""
<style>
/* Compact header */
.main-header {
    padding: 0.7rem 1.2rem;
    background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%);
    border-radius: 10px;
    margin-bottom: 1rem;
}
.main-header h1 {
    color: white;
    font-size: 1.2rem;
    margin: 0;
}
.main-header p {
    color: #DBEAFE;
    margin: 0;
    font-size: 0.78rem;
}

/* Sidebar app items */
.app-item {
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    background: white;
    border-left: 3px solid transparent;
}
.app-item:hover {
    background: #EFF6FF;
    border-left: 3px solid #2563EB;
}
.app-company {
    font-weight: 600;
    font-size: 0.85rem;
    color: #1E293B;
}
.app-role {
    font-size: 0.75rem;
    color: #64748B;
}

/* Inputs and buttons */
div[data-testid="stTextArea"] textarea { border-radius: 10px; }
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
""", unsafe_allow_html=True)

# ---------- PDF extraction ----------
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

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

# ---------- Status badge helper ----------
def status_badge(status):
    badges = {
        "Applied": "🔵 Applied",
        "Interview Scheduled": "🟢 Interview",
        "Offer": "🟡 Offer",
        "Rejected": "🔴 Rejected"
    }
    return badges.get(status, status)

# ---------- Sidebar (Claude-style) ----------
with st.sidebar:
    st.markdown("## 💼 Job Agent")
    st.button("➕ New Application", use_container_width=True)
    st.markdown("---")
    st.markdown("#### 📋 Applications")

    applications = load_applications()

    if not applications:
        st.caption("No applications yet.")
    else:
        for status_group in ["Applied", "Interview Scheduled", "Offer", "Rejected"]:
            group = [a for a in applications if a['status'] == status_group]
            if group:
                st.markdown(f"**{status_badge(status_group)}**")
                for app in group:
                    st.markdown(f"""
                    <div class="app-item">
                        <div class="app-company">{app['company']}</div>
                        <div class="app-role">{app['role']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    st.write("[GitHub](https://github.com/mujeeb-ullah-khan/job-application-assistant-agent)")
    st.caption("Built by Mujeeb Ullah Khan")

# ---------- Compact header ----------
st.markdown("""
<div class="main-header">
    <h1>💼 Job/Internship Application Assistant Agent</h1>
    <p>AI-powered cover letters, skill matching & application tracking</p>
</div>
""", unsafe_allow_html=True)

# ---------- UI: Tabs ----------
tab1, tab2, tab3 = st.tabs(["✍️ Generate Cover Letter", "📋 Application Tracker", "📊 Statistics"])

# --- Tab 1: Cover letter generator ---
with tab1:
    st.subheader("Add your resume and a job posting")

    uploaded_pdf = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])
    pasted_resume = st.text_area(
        "✍️ Or paste your resume here",
        height=150,
        placeholder="Paste your resume text here..."
    )

    resume_text = ""
    if uploaded_pdf is not None:
        resume_text = extract_text_from_pdf(uploaded_pdf)
        st.success("✅ Resume extracted from PDF!")
        with st.expander("Preview extracted text"):
            st.write(resume_text)
    elif pasted_resume.strip():
        resume_text = pasted_resume
        st.info("Using pasted resume text.")

    job_posting_text = st.text_area(
        "📋 Job Posting",
        height=200,
        placeholder="Paste the job posting here..."
    )

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
            with st.expander(f"{app['role']} at {app['company']} — {status_badge(app['status'])}"):
                st.write(f"**Date applied:** {app['date_applied']}")
                st.write(f"**Notes:** {app['notes'] if app['notes'] else 'None'}")
                new_status = st.selectbox(
                    "Update status",
                    ["Applied", "Interview Scheduled", "Offer", "Rejected"],
                    index=["Applied", "Interview Scheduled", "Offer", "Rejected"].index(
                        app['status']
                    ) if app['status'] in ["Applied", "Interview Scheduled", "Offer", "Rejected"] else 0,
                    key=f"status_{i}"
                )
                if st.button("Update", key=f"update_{i}"):
                    update_application_status(app['company'], app['role'], new_status)
                    st.success("Updated! Refresh to see changes.")

# --- Tab 3: Statistics ---
with tab3:
    st.subheader("📊 Application Statistics")
    applications = load_applications()

    if not applications:
        st.info("No applications logged yet. Start tracking to see statistics.")
    else:
        total = len(applications)
        applied = len([a for a in applications if a['status'] == "Applied"])
        interview = len([a for a in applications if a['status'] == "Interview Scheduled"])
        offer = len([a for a in applications if a['status'] == "Offer"])
        rejected = len([a for a in applications if a['status'] == "Rejected"])

        # Metric cards
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📁 Total", total)
        col2.metric("🔵 Applied", applied)
        col3.metric("🟢 Interview", interview)
        col4.metric("🟡 Offer", offer)
        col5.metric("🔴 Rejected", rejected)

        st.divider()

        # Bar chart
        df = pd.DataFrame({
            "Status": ["Applied", "Interview", "Offer", "Rejected"],
            "Count": [applied, interview, offer, rejected]
        })
        st.bar_chart(df.set_index("Status"))

        st.divider()

        # Recent applications
        st.subheader("🕐 Recent Applications")
        recent = sorted(applications, key=lambda x: x['date_applied'], reverse=True)[:5]
        for app in recent:
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.write(f"**{app['company']}**")
            col2.write(app['role'])
            col3.write(status_badge(app['status']))
