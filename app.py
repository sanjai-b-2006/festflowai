import streamlit as st
import pandas as pd
import plotly.express as px
import mock_api as api
from ui_components import render_expense_card
import ocr_processor
import report_generator

# Initialize database and page config
api.setup_database()
st.set_page_config(page_title="FestFlow AI Pro", page_icon="💸", layout="wide")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css("styles.css")

# --- State Management ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def main():
    if not st.session_state.logged_in:
        display_login_form()
    else:
        display_main_app()

def display_login_form():
    st.title("💸 Welcome to FestFlow AI Pro")
    st.caption("Advanced Expense Management with OCR and PDF Reporting")
    
    login_options = api.get_all_usernames()
    if not login_options:
        st.error("User database is not initialized. Please restart the app or check the db_users.json file.")
        return

    username = st.selectbox("Select user to log in as", login_options)
    password = st.text_input("Password", type="password", value="")

    if st.button("Login", use_container_width=True, type="primary"):
        user = api.authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_info = user
            st.rerun()
        else:
            st.error("Invalid credentials. Please check the password.")

def display_main_app():
    user = st.session_state.user_info
    current_event = api.get_events_for_user(user)[0]

    with st.sidebar:
        st.title(f"💸 {current_event['name']}")
        st.write(f"Welcome, **{user['name']}**")
        st.caption(f"Role: {user['role'].replace('_', ' ').title()}")
        st.divider()

        menu_options = []

        if user['role'] == 'student':
            menu_options.append("Submit Expense")
        if user['role'] in ['team_lead', 'treasurer']:
            menu_options.append("Manage Approvals")
        if user['role'] == 'treasurer':
            menu_options.insert(0, "Dashboard") 

        menu_options.append("My Submitted Expenses")
        
        if user['role'] == 'treasurer':
             menu_options.extend(["Generate Report", "Activity Log"])
        
        page = st.radio("Navigation", menu_options, label_visibility="hidden")
        
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    title, notif_area = st.columns([4, 1])
    with title:
        st.header(page)
    with notif_area:
        pending_count = len(api.get_pending_requests(user['role']))
        if pending_count > 0:
            st.success(f"**Action Required!**\nYou have **{pending_count}** request(s) waiting.", icon="🔔")

    if page == "Dashboard":
        render_dashboard(current_event)
    elif page == "Submit Expense":
        render_submit_expense_form(current_event, user)
    elif page == "My Submitted Expenses":
        render_expense_list(user, my_expenses=True)
    elif page == "Manage Approvals":
        render_expense_list(user, my_expenses=False)
    elif page == "Generate Report":
        render_report_page(current_event)
    elif page == "Activity Log":
        render_activity_log_page()

def render_dashboard(event):
    st.markdown("A real-time overview of the event's financial health and activity.")
    st.divider()

    all_expenses = api.parse_datetimes(api.load_data(api.EXPENSES_FILE))
    
    if not all_expenses:
        st.info("No expenses have been submitted yet. The dashboard will populate as data comes in.")
        return
        
    df = pd.DataFrame(all_expenses)
    df['submitted_date'] = df['submitted_at'].dt.date

    st.subheader("Financial Overview")
    total_budget = event['budget']
    total_spent = df[df['status'].isin(['Approved', 'Reimbursed'])]['amount'].sum()
    remaining = total_budget - total_spent
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Budget", f"₹{total_budget:,.0f}")
    kpi2.metric("Total Spent (Approved & Reimbursed)", f"₹{total_spent:,.0f}", f"-{total_spent/total_budget if total_budget>0 else 0:.1%}")
    kpi3.metric("Remaining Budget", f"₹{remaining:,.0f}")
    st.progress(total_spent / total_budget if total_budget > 0 else 0)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spending by Category")
        if total_spent > 0:
            category_spend = df[df['status'].isin(['Approved', 'Reimbursed'])].groupby('category')['amount'].sum()
            fig_pie = px.pie(category_spend, values='amount', names=category_spend.index, hole=0.4)
            fig_pie.update_layout(showlegend=True, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No approved spending yet.")

        st.subheader("Top Spenders (by total amount submitted)")
        user_spend = df.groupby('user')['amount'].sum().sort_values(ascending=True).tail(5)
        fig_bar_h = px.bar(user_spend, x='amount', y=user_spend.index, orientation='h', labels={'amount': 'Total Amount (₹)', 'y': 'User'})
        fig_bar_h.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar_h, use_container_width=True)

    with col2:
        st.subheader("Cumulative Spending Over Time")
        daily_spend = df[df['status'].isin(['Approved', 'Reimbursed'])].groupby('submitted_date')['amount'].sum().cumsum().reset_index()
        fig_line = px.line(daily_spend, x='submitted_date', y='amount', markers=True, labels={'submitted_date': 'Date', 'amount': 'Cumulative Spend (₹)'})
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.subheader("Expense Workflow Status")
        status_counts = df['status'].value_counts()
        fig_bar = px.bar(status_counts, x=status_counts.index, y=status_counts.values, labels={'x': 'Status', 'y': 'Number of Expenses'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()

    st.subheader("Average Expense Amount per Category")
    avg_cat_spend = df.groupby('category')['amount'].mean().sort_values(ascending=False).reset_index()
    fig_funnel = px.funnel(avg_cat_spend, x='amount', y='category', labels={'amount': 'Average Amount (₹)', 'category': 'Category'})
    st.plotly_chart(fig_funnel, use_container_width=True)


def render_submit_expense_form(event, user):
    st.subheader("Upload a receipt to auto-scan details")
    receipt_file = st.file_uploader("Upload Receipt", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if 'ocr_amount' not in st.session_state: st.session_state.ocr_amount = 0.0
    if receipt_file and st.button("Scan Receipt with OCR"):
        with st.spinner("Analyzing receipt..."):
            ocr_result = ocr_processor.process_receipt(receipt_file)
            st.session_state.ocr_amount = ocr_result.get('amount', 0.0)
            if st.session_state.ocr_amount > 0:
                st.success(f"Successfully scanned amount: ₹{st.session_state.ocr_amount}", icon="✅")
            else:
                st.warning("Could not automatically detect amount. Please enter manually.", icon="⚠️")
    with st.form("expense_form", clear_on_submit=True):
        initial_value = st.session_state.ocr_amount if st.session_state.ocr_amount > 0 else None
        amount = st.number_input("Amount (₹)", min_value=0.01, value=initial_value, format="%.2f")
        category = st.selectbox("Category", ["Decorations", "Printing", "Logistics", "Food & Beverages", "Prizes", "Stationery"])
        description = st.text_area("Description of Expense")
        submitted = st.form_submit_button("Submit for Approval", use_container_width=True, type="primary")
        if submitted:
            if not receipt_file: st.error("A receipt upload is mandatory.")
            elif not description: st.warning("Please provide a description.")
            else:
                api.add_expense(event['id'], user, amount, category, description, receipt_file)
                st.success("Expense submitted for Team Lead approval!")
                st.session_state.ocr_amount = 0.0

def render_expense_list(user, my_expenses=False):
    if my_expenses:
        st.caption("Track the status of all expenses you have submitted.")
        expense_list = api.get_expenses_for_user(user['username'])
    else:
        st.caption("Review and action expenses waiting for your attention.")
        expense_list = api.get_pending_requests(user['role'])

    if not expense_list:
        st.info("There are no expenses to display in this view.")
        return

    def on_update():
        st.rerun()

    expense_list.sort(key=lambda x: x['submitted_at'], reverse=True)

    for expense in expense_list:
        render_expense_card(expense, user, on_update)

def render_report_page(event):
    st.info("Generate a final, consolidated report for all reimbursed expenses.")

    expenses_df = pd.DataFrame(api.parse_datetimes(api.load_data(api.EXPENSES_FILE)))
    
    # Filter for ONLY reimbursed expenses here, before passing to the report generators.
    reimbursed_df = expenses_df[expenses_df['status'] == 'Reimbursed'].copy()

    if reimbursed_df.empty:
        st.warning("There are no reimbursed expenses to report on yet.")
        return 

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬇️ Generate PDF Report", use_container_width=True):
            with st.spinner("Compiling data and creating your PDF report..."):
                pdf_data = report_generator.generate_report(event, reimbursed_df)
            st.success("PDF Report Generated!")
            st.download_button(
                "Download PDF", 
                pdf_data, 
                f"{event['name']}_Financial_Report.pdf", 
                "application/pdf",
                key="pdf_download"
            )

    with col2:
        if st.button("📄 Generate JSON Report", use_container_width=True, type="primary"):
            with st.spinner("Compiling data and creating your JSON report..."):
                json_data = report_generator.generate_json_report(event, reimbursed_df)
            st.success("JSON Report Generated!")
            st.download_button(
                "Download JSON",
                json_data,
                f"{event['name']}_Financial_Report.json",
                "application/json",
                key="json_download"
            )

def render_activity_log_page():
    st.caption("A complete, immutable audit trail of all actions performed in the system.")
    log_data = api.get_activity_log()
    if not log_data:
        st.info("No activity has been logged yet.")
        return
    for log in log_data:
        with st.container(border=True):
            st.markdown(f"**{log['user']}** {log['action']}")
            st.caption(log['timestamp'].strftime('%d %b %Y, %I:%M:%S %p'))

if __name__ == "__main__":
    main()