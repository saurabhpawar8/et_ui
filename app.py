from datetime import date

import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Expense Tracker AI", page_icon="💰", layout="centered")

# Session State
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "registered" not in st.session_state:
    st.session_state["registered"] = False


# API Helpers
def login(email, password):
    try:
        r = requests.post(
            f"{BACKEND_URL}/account/auth/login/",
            json={"email": email, "password": password},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json().get("message"), None
        return None, r.json().get("detail", "Invalid credentials")
    except Exception as e:
        return None, str(e)


def register(email, password):
    try:
        r = requests.post(
            f"{BACKEND_URL}/account/auth/register/",
            json={"email": email, "password": password},
            timeout=30,
        )
        if r.status_code in [200, 201]:
            return True, None
        return False, r.json().get("detail") or str(r.json())
    except Exception as e:
        return False, str(e)


def send_message(message, token):
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/chat/",
            json={"query": message},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json().get("message"), None
        return None, f"Error {r.status_code}: {r.text}"
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except Exception as e:
        return None, str(e)


def get_report(token, month):
    try:
        r = requests.post(
            f"{BACKEND_URL}/report/expense_report/",
            json={"month": month},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
        if r.status_code == 200:
            return r.json(), None
        return None, f"Error {r.status_code}: {r.text}"
    except requests.exceptions.Timeout:
        return None, "Report generation timed out. Please try again."
    except Exception as e:
        return None, str(e)


def extract_document(token, file):
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/extract_doc/",
            files={"file": (file.name, file, file.type)},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
        if r.status_code == 200:
            return r.json(), None
        return None, f"Error {r.status_code}: {r.text}"
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except Exception as e:
        return None, str(e)


# Login Page
def show_login():
    st.title("💰 Expense Tracker AI")
    st.markdown("Your personal AI-powered finance assistant")
    st.divider()
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button(
            "Login", use_container_width=True, type="primary"
        )
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                with st.spinner("Logging in..."):
                    data, error = login(email, password)
                    if data:
                        print(data)
                        st.session_state["access_token"] = data["data"]["access"]
                        st.session_state["messages"] = []
                        st.session_state["page"] = "chat"
                        st.rerun()
                    else:
                        st.error(f"Login failed: {error}")
    st.divider()
    st.markdown("Don't have an account?")
    if st.button("Register here", use_container_width=True):
        st.session_state["page"] = "register"
        st.rerun()


# Register Page
def show_register():
    st.title("💰 Create Account")
    st.divider()
    if st.session_state["registered"]:
        st.success("Registration successful!")
        if st.button("Click here to Login", use_container_width=True, type="primary"):
            st.session_state["registered"] = False
            st.session_state["page"] = "login"
            st.rerun()
        return
    with st.form("register_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        confirm = st.text_input(
            "Confirm Password", type="password", placeholder="••••••••"
        )
        submitted = st.form_submit_button(
            "Register", use_container_width=True, type="primary"
        )
        if submitted:
            if not email or not password or not confirm:
                st.error("Please fill in all fields")
            elif password != confirm:
                st.error("Passwords do not match")
            else:
                with st.spinner("Creating account..."):
                    success, error = register(email, password)
                    if success:
                        st.session_state["registered"] = True
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {error}")
    st.divider()
    if st.button("Login here", use_container_width=True):
        st.session_state["page"] = "login"
        st.rerun()


# Report Page
def show_report():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📊 Financial Report")
    with col2:
        if st.button("← Back"):
            st.session_state["page"] = "chat"
            st.rerun()

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox(
            "Year",
            options=[2024, 2025, 2026, 2027],
            index=[2024, 2025, 2026, 2027].index(date.today().year),
        )
    with col2:
        months = {
            "January": "01",
            "February": "02",
            "March": "03",
            "April": "04",
            "May": "05",
            "June": "06",
            "July": "07",
            "August": "08",
            "September": "09",
            "October": "10",
            "November": "11",
            "December": "12",
        }
        selected_month_name = st.selectbox(
            "Month", options=list(months.keys()), index=date.today().month - 1
        )
    selected_month = f"{selected_year}-{months[selected_month_name]}"
    st.caption(f"Selected period: **{selected_month_name} {selected_year}**")

    if st.button("Generate Report", type="primary", use_container_width=True):
        with st.spinner(
            "Generating your financial health report... This may take 15-20 seconds."
        ):
            data, error = get_report(st.session_state["access_token"], selected_month)
            if error:
                st.error(f"Failed to generate report: {error}")
            else:
                render_report(data)


def render_report(data):
    st.divider()
    score = data.get("health_score", 0)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏆 Health Score", f"{score}/10")
    with col2:
        st.metric("💸 Total Expenses", f"₹{data.get('total_expense', 0):,.2f}")
    with col3:
        st.metric("📂 Categories", len(data.get("breakdown", [])))

    st.divider()
    st.subheader("🏆 Financial Health")
    score_icon = "🟢" if score >= 7 else "🟡" if score >= 4 else "🔴"
    score_label = (
        "Excellent"
        if score >= 8
        else "Good"
        if score >= 6
        else "Average"
        if score >= 4
        else "Poor"
    )
    st.markdown(f"### {score_icon} {score}/10 — {score_label}")
    st.progress(score / 10)

    st.divider()
    st.subheader("📈 Spending Breakdown")
    breakdown = data.get("breakdown", [])
    if breakdown:
        total = sum(item.get("total", 0) for item in breakdown)
        for item in breakdown:
            category = item.get("category_name", "Unknown")
            amount = item.get("total", 0)
            pct = (amount / total * 100) if total > 0 else 0
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(pct / 100, text=f"{category}")
            with col2:
                st.markdown(f"**₹{amount:,.0f}** ({pct:.1f}%)")
    else:
        st.info("No spending data found for this month.")

    st.divider()
    st.subheader("🔍 Key Patterns")
    st.info(data.get("patterns", "No patterns identified."))

    st.subheader("📊 Spending Trend")
    st.warning(data.get("spending_trend", "No trend data."))

    st.subheader("🏅 Top Category")
    st.markdown(data.get("top_category", "No data."))

    st.divider()
    st.subheader("💡 Suggestions")
    suggestions = data.get("suggestions", [])
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            st.success(f"**{i}.** {s}")
    else:
        st.info("No suggestions available.")

    st.divider()
    with st.expander("📄 View Full Report", expanded=False):
        st.markdown(data.get("report", "No report generated."))


# Document Extractor Page
def show_document():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📄 Document Extractor")
    with col2:
        if st.button("← Back"):
            st.session_state["page"] = "chat"
            st.rerun()

    st.markdown("Upload a bank statement or financial document to get a summary.")
    st.divider()

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "csv", "xlsx", "xls"],
        help="Supported formats: PDF, CSV, Excel",
    )

    if uploaded_file:
        st.success(
            f"✅ File selected: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)"
        )
        if st.button("Extract & Summarize", type="primary", use_container_width=True):
            with st.spinner("Analyzing your document..."):
                data, error = extract_document(
                    st.session_state["access_token"], uploaded_file
                )
                if error:
                    st.error(f"Failed: {error}")
                else:
                    st.divider()
                    date_range = data.get("date_range", "")
                    if date_range:
                        st.info(f"📅 **Period:** {date_range}")
                    st.subheader("📋 Summary")
                    st.markdown(data.get("summary", "No summary available."))
                    st.divider()
                    summary_text = f"Date Range: {date_range}\n\nSummary:\n{data.get('summary', '')}"
                    st.download_button(
                        label="⬇️ Download Summary",
                        data=summary_text,
                        file_name=f"summary_{uploaded_file.name}.txt",
                        mime="text/plain",
                    )
    else:
        st.info("👆 Please upload a file to get started.")


# Chat Page
def show_chat():
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.title("💰 Expense Assistant")
    with col2:
        if st.button("📊 Report", use_container_width=True):
            st.session_state["page"] = "report"
            st.rerun()
    with col3:
        if st.button("📄 Docs", use_container_width=True):
            st.session_state["page"] = "document"
            st.rerun()
    with col4:
        if st.button("Logout", use_container_width=True):
            st.session_state["access_token"] = None
            st.session_state["messages"] = []
            st.session_state["page"] = "login"
            st.rerun()

    st.markdown("Ask me to save expenses or query your spending history.")
    st.divider()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(
        "e.g. 'Spent 200 at Zomato' or 'How much did I spend this month?'"
    )
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, error = send_message(
                    user_input, st.session_state["access_token"]
                )
                if error:
                    if "401" in str(error) or "403" in str(error):
                        st.error("Session expired. Please login again.")
                        st.session_state["access_token"] = None
                        st.session_state["page"] = "login"
                        st.rerun()
                    else:
                        msg = f"Sorry, something went wrong: {error}"
                        st.markdown(msg)
                        st.session_state["messages"].append(
                            {"role": "assistant", "content": msg}
                        )
                else:
                    print(response)
                    st.markdown(response)
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": response}
                    )


# Router
if not st.session_state["access_token"]:
    if st.session_state["page"] == "register":
        show_register()
    else:
        show_login()
elif st.session_state["page"] == "report":
    show_report()
elif st.session_state["page"] == "document":
    show_document()
else:
    show_chat()
