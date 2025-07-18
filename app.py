import streamlit as st
import pandas as pd
import plotly.express as px
import mock_api as api
from ui_components import render_expense_card
import ocr_processor
import report_generator
import predictions 
import datetime

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
            menu_options.append("My Submitted Expenses")
            menu_options.append("Request Advance")
            menu_options.append("My Advances")
            menu_options.append("Edit My UPI ID")  # if present

        if user['role'] in ['team_lead', 'treasurer']:
            menu_options.append("My Approvals")  # <-- NEW
            menu_options.append("Manage Approvals")
            menu_options.append("Approve Advances")

        if user['role'] == 'treasurer':
            menu_options.insert(0, "Dashboard")
            menu_options.extend(["Generate Report", "Activity Log"])

        page = st.radio("Navigation", menu_options, label_visibility="hidden")

        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
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
    elif page == "My Approvals":
        render_my_approvals(user)  # <-- New handler function
    elif page == "Generate Report":
        render_report_page(current_event)
    elif page == "Approve Advances":
        render_advances_for_approval(user)
    elif page == "Request Advance":
        render_request_advance_form(current_event, user)
    elif page == "My Advances":
        render_advance_list(user)
    elif page == "Activity Log":
        render_activity_log_page()
    elif page == "Edit My UPI ID":  # ✅ NEW PAGE ROUTE
        render_upi_editor_student(user)

def render_advances_for_approval(user):
    st.subheader("Approve Advance Requests")
    all_advances = api.load_data("db_advances.json")

    # Filter for pending advances team_lead or treasurer need to act on
    shown = []
    for adv in all_advances:
        if user['role'] == "team_lead" and adv['status'] == "Pending":
            shown.append(adv)
        elif user['role'] == "treasurer" and adv['status'] == "Approved by Team Lead":
            shown.append(adv)

    if not shown:
        st.info("No advance requests require your attention.")
        return

    shown.sort(key=lambda a: a['id'], reverse=True)

    for adv in shown:
        with st.container(border=True):
            st.markdown(f"**Vendor:** {adv['vendor']} | ₹{adv['amount']:.2f}")
            st.caption(f"Purpose: {adv['purpose']}")
            st.caption(f"Requested By: {adv['user']}")
            if adv.get('quote_url'):
                st.markdown(f"[🧾 View Quote]({adv['quote_url']})")

            if user['role'] == "team_lead":
                from streamlit import markdown
                st.markdown('<div class="approve-reject-row">', unsafe_allow_html=True)
                approve_col, reject_col = st.columns(2)
                with approve_col:
                    if st.button("Approve", key=f"a{adv['id']}"):
                        adv['status'] = "Approved by Team Lead"
                        adv['approved_by'] = user['name']
                        api.save_data("db_advances.json", all_advances)
                        api.log_activity(user['name'], f"approved advance #{adv['id']}")
                        st.success("Approved.")
                        st.rerun()
                with reject_col:
                    if st.button("Reject", key=f"r{adv['id']}"):
                        adv['status'] = "Rejected"
                        api.save_data("db_advances.json", all_advances)
                        api.log_activity(user['name'], f"rejected advance #{adv['id']}")
                        st.warning("Rejected.")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            elif user['role'] == "treasurer" and adv['status'] == "Approved by Team Lead":
                txn_col, button_col = st.columns([3, 1])
                txn_id = txn_col.text_input("Transaction ID / Reference", key=f"txn{adv['id']}")
                if button_col.button("💸 Mark as Paid", key=f"pay{adv['id']}"):
                    if not txn_id:
                        st.warning("Please provide a transaction ID.")
                    else:
                        adv['status'] = "Paid"
                        adv['paid_txn_id'] = txn_id
                        adv['paid_time'] = datetime.datetime.now().isoformat()
                        adv['paid_by'] = user['name']       # <--- Save who paid!
                        api.save_data("db_advances.json", all_advances)
                        api.log_activity(user['name'], f"marked advance #{adv['id']} as paid (txn: {txn_id})")
                        st.success("Marked as Paid.")
                        st.rerun()

def render_request_advance_form(event, user):
    st.subheader("Request an Advance")
    with st.form("advance_form"):
        vendor = st.text_input("Vendor Name or Service")
        purpose = st.text_area("Purpose / What is this Advance For?")
        amount = st.number_input("Advance Amount Needed (₹)", min_value=0.0)
        quote_file = st.file_uploader("Upload Vendor Quote (Optional)", type=["jpg", "jpeg", "png", "pdf"])
        submitted = st.form_submit_button("Submit Advance Request")

        if submitted:
            if not vendor or not purpose:
                st.warning("Vendor and purpose are required.")
            else:
                api.add_advance_request(user, event['id'], vendor, purpose, amount, quote_file)
                st.success("Advance request submitted.")

def render_advance_list(user):
    st.subheader("My Advance Requests")
    advances = api.get_advances_for_user(user['username'])

    if not advances:
        st.info("You have not submitted any advance requests yet.")
        return

    advances.sort(key=lambda x: x['submitted_at'], reverse=True)

    for adv in advances:
        with st.container(border=True):
            st.markdown(f"**Vendor:** {adv['vendor']} | **Amount:** ₹{adv['amount']:.2f}")
            st.caption(f"Status: {adv['status']} | Submitted: {adv['submitted_at'].strftime('%d %b %Y')}")
            st.markdown(f"*Purpose:* {adv['purpose']}")
            if adv.get('quote_url'):
                st.markdown(f"[🧾 View Uploaded Quote]({adv['quote_url']})")
            if adv['status'] == "Paid" and not adv.get('receipt_url'):
                with st.form(key=f"close_adv_{adv['id']}"):
                    receipt = st.file_uploader("Upload Final Receipt", type=["pdf", "jpg", "jpeg", "png"])
                    done = st.form_submit_button("Close Advance")
                    if done and receipt:
                        api.close_advance(adv['id'], user, receipt)
                        st.success("Advance marked as completed.")

def suggest_category(ocr_text):
    ocr_text_lower = ocr_text.lower()
    keywords = [
        (["zomato", "swiggy", "restaurant", "food", "beverages"], "Food & Beverages"),
        (["print", "xerox", "banner", "poster", "flex"], "Printing"),
        (["stationery", "pen", "notebook"], "Stationery"),
        (["cab", "auto", "ola", "uber", "transport"], "Logistics"),
        (["trophy", "gift", "medal", "prize"], "Prizes"),
        (["decoration", "floral", "balloon"], "Decorations")
    ]
    for words, category in keywords:
        if any(word in ocr_text_lower for word in words):
            return category
    return "Miscellaneous"

def render_my_approvals(user):
    st.header("My Approvals")

    # Expenses (as before)
    all_expenses = api.parse_datetimes(api.load_data(api.EXPENSES_FILE))
    approvals = []
    for expense in all_expenses:
        for step in expense.get('approvals', []):
            # Only add if this approval step was completed by you
            if step.get('approved_by') == user['name']:
                approvals.append(expense)
                break


    st.subheader("Expense Approvals")
    if not approvals:
        st.info("No expenses found for your approval or previously approved.")
    else:
        approvals.sort(key=lambda x: x['submitted_at'], reverse=True)
        def on_update_exp():
            st.rerun()
        for expense in approvals:
            render_expense_card(expense, user, on_update_exp)

    # Advances
    all_advances = api.load_data("db_advances.json")
    st.subheader("Advance Requests You've Approved")

    if user['role'] == "team_lead":
        advances_to_show = [a for a in all_advances if a.get('status') in {"Approved by Team Lead", "Paid"} and a.get('approved_by') == user['name']]
    elif user['role'] == "treasurer":
        advances_to_show = [a for a in all_advances if a.get('status') == "Paid" and a.get('paid_by') == user['name']]
    else:
        advances_to_show = []

    from ui_components import render_advance_card
    for adv in advances_to_show:
        render_advance_card(adv)

def render_upi_editor_student(user):
    st.subheader("Edit Your UPI ID")
    users = api.load_data(api.USERS_FILE)

    # Find logged-in user in the user list
    current_user = next((u for u in users if u['username'] == user['username']), None)

    if not current_user:
        st.error("User not found in records.")
        return

    with st.form("upi_update_form_student"):
        new_upi = st.text_input("Your UPI ID", value=current_user.get('upi_id', ''))
        submitted = st.form_submit_button("Update")

        if submitted:
            current_user['upi_id'] = new_upi.strip()
            api.save_data(api.USERS_FILE, users)
            st.success("Your UPI ID has been updated successfully.")

def render_dashboard(event):
    st.markdown("A real-time overview of the event's financial health and activity.")
    st.divider()

    all_expenses_raw = api.load_data(api.EXPENSES_FILE)
    if not all_expenses_raw:
        st.info("No expenses have been submitted yet. The dashboard will populate as data comes in.")
        return
    
    all_expenses = api.parse_datetimes(all_expenses_raw)
    df = pd.DataFrame(all_expenses)

    # --- THE MAIN DATAFRAME CLEANING STEP ---
    # 1. Force conversion to datetime, turning any errors into 'NaT' (Not a Time)
    df['submitted_at'] = pd.to_datetime(df['submitted_at'], errors='coerce')
    # 2. Force 'amount' to numeric, turning errors into 0
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    # 3. Drop any rows where the date conversion failed
    df.dropna(subset=['submitted_at'], inplace=True)
    # --- END OF CLEANING ---

    # --- Financial Overview KPIs ---
    st.subheader("Financial Overview")
    total_budget = event['budget']
    total_spent = df[df['status'].isin(['Approved', 'Reimbursed'])]['amount'].sum()
    remaining_budget = total_budget - total_spent
    
    # Predictive Analytics Section
    forecast_fig, projected_total = predictions.generate_forecast_chart(event, df.copy())
    projected_surplus = total_budget - projected_total
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Budget", f"₹{total_budget:,.0f}")
    kpi2.metric("Total Spent (Actual)", f"₹{total_spent:,.0f}", f"-{total_spent/total_budget if total_budget > 0 else 0:.1%}")
    kpi3.metric("Remaining Budget (Actual)", f"₹{remaining_budget:,.0f}")
    kpi4.metric(
        label="Projected Final Spend", 
        value=f"₹{projected_total:,.0f}", 
        delta=f"₹{projected_surplus:,.0f} Projected Surplus" if projected_surplus >= 0 else f"₹{abs(projected_surplus):,.0f} Projected Deficit",
        delta_color="normal" if projected_surplus >= 0 else "inverse"
    )
    st.progress(total_spent / total_budget if total_budget > 0 else 0)
    st.divider()

    # Combined Forecast Chart
    st.plotly_chart(forecast_fig, use_container_width=True)
    st.divider()
    
    # Other Dashboard Components
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spending by Category (Approved)")
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
        st.subheader("Expense Workflow Status")
        status_counts = df['status'].value_counts()
        fig_bar = px.bar(status_counts, x=status_counts.index, y=status_counts.values, labels={'x': 'Status', 'y': 'Number of Expenses'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.subheader("Average Expense Amount per Category")
        if not df.empty:
            avg_cat_spend = df.groupby('category')['amount'].mean().sort_values(ascending=False).reset_index()
            fig_funnel = px.funnel(avg_cat_spend, x='amount', y='category', labels={'amount': 'Average Amount (₹)', 'category': 'Category'})
            st.plotly_chart(fig_funnel, use_container_width=True)

def render_submit_expense_form(event, user):
    st.subheader("Upload a receipt to auto-scan details")
    receipt_file = st.file_uploader("Upload Receipt", type=["png", "jpg", "jpeg","webp"], label_visibility="collapsed")
    if 'ocr_amount' not in st.session_state: st.session_state.ocr_amount = 0.0
    if receipt_file and st.button("Scan Receipt with OCR"):
        with st.spinner("Analyzing receipt..."):
            ocr_result = ocr_processor.process_receipt(receipt_file)
            st.session_state.ocr_amount = ocr_result.get('amount', 0.0)
            if st.session_state.ocr_amount > 0:
                st.success(f"Successfully scanned amount: ₹{st.session_state.ocr_amount}", icon="✅")
                st.session_state.ocr_text = ocr_result.get('text', '')
                st.session_state.suggested_category = suggest_category(st.session_state.ocr_text)
                st.info(f"Suggested Category: **{st.session_state.suggested_category}**")
            else:
                st.warning("Could not automatically detect amount. Please enter manually.", icon="⚠️")
                st.session_state.ocr_text = ''

    with st.form("expense_form", clear_on_submit=True):
        initial_value = st.session_state.ocr_amount if st.session_state.ocr_amount > 0 else None
        amount = st.number_input("Amount (₹)", min_value=0.01, value=initial_value, format="%.2f")
        categories = ["Decorations", "Printing", "Logistics", "Food & Beverages", "Prizes", "Stationery", "Miscellaneous"]
        default_category = st.session_state.get("suggested_category", categories[0])
        category = st.selectbox("Category", categories, index=categories.index(default_category) if default_category in categories else 0)
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
        st.info("No expenses found.")
        return

    # -------- FILTER UI --------
    description_query = st.text_input("🔍 Search Description...")
    statuses = sorted(list(set(e['status'] for e in expense_list)))
    selected_statuses = st.multiselect("Filter by Status:", statuses, default=statuses)
    amounts = [e['amount'] for e in expense_list]
    amt_min, amt_max = st.slider("Filter by Amount", 0.0, max(amounts + [0]), (0.0, max(amounts + [0])), step=0.5)
    # -------- FILTERING --------
    filtered_expenses = []
    for e in expense_list:
        if description_query.lower() not in e['description'].lower():
            continue
        if e['status'] not in selected_statuses:
            continue
        if not (amt_min <= e['amount'] <= amt_max):
            continue
        filtered_expenses.append(e)

    if not filtered_expenses:
        st.warning("No matching results found.")
        return

    filtered_expenses.sort(key=lambda x: x['submitted_at'], reverse=True)

    def on_update(): st.rerun()
    for e in filtered_expenses:
        render_expense_card(e, user, on_update)

def render_report_page(event):
    st.info("Generate a final, consolidated report for all reimbursed expenses.")

    expenses_df_raw = api.parse_datetimes(api.load_data(api.EXPENSES_FILE))
    expenses_df = pd.DataFrame(expenses_df_raw)
    
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
            # Robustly display timestamp
            ts_str = log.get('timestamp').strftime('%d %b %Y, %I:%M:%S %p') if log.get('timestamp') else 'N/A'
            st.caption(ts_str)

if __name__ == "__main__":
    main()