from datetime import date
import requests
import streamlit as st

BACKEND_URL = "https://aiexpensetracker-production-c445.up.railway.app"

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
if "summary" not in st.session_state:
    st.session_state["summary"] = None
if "pie_data" not in st.session_state:
    st.session_state["pie_data"] = None

# Persist token across refresh using query params
params = st.query_params
if "token" in params and not st.session_state["access_token"]:
    st.session_state["access_token"] = params["token"]
    st.session_state["page"] = "chat"


# API Helpers
def login(email, password):
    try:
        r = requests.post(
            f"{BACKEND_URL}/account/auth/login/",
            json={"email": email, "password": password},
            timeout=30,
        )
        if r.status_code in [200, 201]:
            body = r.json()
            if body.get("success"):
                return body.get("data"), None
            return None, body.get("message", "Invalid credentials")
        return None, r.json().get("message", "Invalid credentials")
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
            body = r.json()
            if body.get("success"):
                return True, None
            return False, body.get("message", "Registration failed")
        return False, r.json().get("message", "Registration failed")
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
            body = r.json()
            return body.get("message") or body.get("data"), None
        return None, f"Error {r.status_code}: {r.text}"
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except Exception as e:
        return None, str(e)


def get_summary(token):
    try:
        r = requests.get(
            f"{BACKEND_URL}/api/transaction/summary/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            body = r.json()
            if body.get("success"):
                return body.get("data"), None
            return None, body.get("message")
        return None, f"Error {r.status_code}"
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


def get_pie_summary(token):
    try:
        r = requests.get(
            f"{BACKEND_URL}/api/transaction/pie_summary/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            body = r.json()
            if body.get("success"):
                return body.get("data"), None
            return None, body.get("message")
        return None, f"Error {r.status_code}"
    except Exception as e:
        return None, str(e)




# Login Page
def show_login():
    st.title("💰 Expense Tracker AI")
    st.markdown("Your personal AI-powered finance assistant")
    st.divider()

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                with st.spinner("Logging in..."):
                    data, error = login(email, password)
                    if data:
                        st.session_state["access_token"] = data["access"]
                        st.session_state["messages"] = []
                        st.session_state["summary"] = None
                        st.session_state["page"] = "chat"
                        st.query_params["token"] = data["access"]
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
        st.success("✅ Registration successful!")
        st.markdown("You can now login with your credentials.")
        if st.button("Click here to Login", use_container_width=True, type="primary"):
            st.session_state["registered"] = False
            st.session_state["page"] = "login"
            st.rerun()
        return

    with st.form("register_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Register", use_container_width=True, type="primary")

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
    if st.button("Already have an account? Login", use_container_width=True):
        st.session_state["page"] = "login"
        st.rerun()


# Summary Card
def show_summary_card(token):
    if not st.session_state["summary"]:
        data, _ = get_summary(token)
        if data:
            st.session_state["summary"] = data

    summary = st.session_state["summary"]
    if not summary:
        return

    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.markdown(f"### 📅 {summary.get('month', 'This Month')}")
    with col_refresh:
        if st.button("🔄", help="Refresh summary"):
            st.session_state["summary"] = None
            st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💸 Total Spent", f"₹{summary.get('total_expense', 0):,.0f}")
    with col2:
        st.metric("🧾 Transactions", summary.get('total_transactions', 0))
    with col3:
        st.metric(
            "🏆 Top Category",
            summary.get('top_category', 'N/A'),
            delta=f"₹{summary.get('category_amount', 0):,.0f}"
        )
    st.divider()


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
        if st.button("📈 Charts", use_container_width=True):
            st.session_state["page"] = "charts"
            st.rerun()
    with col4:
        if st.button("Logout", use_container_width=True):
            st.session_state["access_token"] = None
            st.session_state["messages"] = []
            st.session_state["summary"] = None
            st.session_state["pie_data"] = None
            st.session_state["page"] = "login"
            st.query_params.clear()
            st.rerun()

    show_summary_card(st.session_state["access_token"])
    st.markdown("Ask me to save expenses or query your spending history.")

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("e.g. 'Spent 200 at Zomato' or 'How much did I spend this month?'")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, error = send_message(user_input, st.session_state["access_token"])
                if error:
                    if "401" in str(error) or "403" in str(error):
                        st.error("Session expired. Please login again.")
                        st.session_state["access_token"] = None
                        st.session_state["page"] = "login"
                        st.rerun()
                    else:
                        msg = f"Sorry, something went wrong: {error}"
                        st.markdown(msg)
                        st.session_state["messages"].append({"role": "assistant", "content": msg})
                else:
                    st.markdown(response)
                    st.session_state["messages"].append({"role": "assistant", "content": response})
                    # refresh summary after every message
                    st.session_state["summary"] = None


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
            "January": "01", "February": "02", "March": "03",
            "April": "04", "May": "05", "June": "06",
            "July": "07", "August": "08", "September": "09",
            "October": "10", "November": "11", "December": "12",
        }
        selected_month_name = st.selectbox(
            "Month", options=list(months.keys()), index=date.today().month - 1
        )
    selected_month = f"{selected_year}-{months[selected_month_name]}"
    st.caption(f"Selected period: **{selected_month_name} {selected_year}**")

    if st.button("Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating your financial health report... This may take 15-20 seconds."):
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
    score_label = "Excellent" if score >= 8 else "Good" if score >= 6 else "Average" if score >= 4 else "Poor"
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




# Charts Page
def show_charts():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📈 Spending Charts")
    with col2:
        if st.button("← Back"):
            st.session_state["page"] = "chat"
            st.rerun()

    st.divider()

    token = st.session_state["access_token"]

    if not st.session_state["pie_data"]:
        data, error = get_pie_summary(token)
        if error:
            st.error(f"Failed to load chart data: {error}")
            return
        if not data:
            st.info("No spending data available yet. Start adding expenses to see charts.")
            return
        st.session_state["pie_data"] = data

    data = st.session_state["pie_data"]
    categories = [item["category_name"] for item in data]
    amounts = [item["total"] for item in data]
    total = sum(amounts)

    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.subheader("🥧 Spending by Category")
    with col_refresh:
        if st.button("🔄", help="Refresh chart", key="refresh_pie"):
            st.session_state["pie_data"] = None
            st.rerun()

    try:
        import plotly.express as px
        import pandas as pd

        df = pd.DataFrame({"Category": categories, "Amount": amounts})
        fig = px.pie(
            df,
            names="Category",
            values="Amount",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
            pull=0
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="v", x=1, y=0.5),
            margin=dict(t=20, b=20, l=20, r=20),
            height=400,
            transition={"duration": 0}
        )
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.warning("Install plotly to see charts: pip install plotly")

    st.divider()
    st.subheader("📋 Category Breakdown")
    for item in sorted(data, key=lambda x: x["total"], reverse=True):
        cat = item["category_name"]
        amt = item["total"]
        pct = (amt / total * 100) if total > 0 else 0
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(pct / 100, text=f"{cat}")
        with col2:
            st.markdown(f"**₹{amt:,.0f}** ({pct:.1f}%)")

    st.divider()
    st.metric("💸 Total This Month", f"₹{total:,.0f}")


# Router
if not st.session_state["access_token"]:
    if st.session_state["page"] == "register":
        show_register()
    else:
        show_login()
elif st.session_state["page"] == "report":
    show_report()
elif st.session_state["page"] == "charts":
    show_charts()
else:
    show_chat()
