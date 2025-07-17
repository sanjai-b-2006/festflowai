import streamlit as st
import os
import mock_api as api

def render_expense_card(expense, user, on_update):
    submitter = api.get_user_details(expense['user'])
    status_map = { "Pending Team Lead": ("#FFC107", "black"), "Pending Treasurer": ("#FFC107", "black"), "Approved": ("#28A745", "white"), "Rejected": ("#DC3545", "white"), "Reimbursed": ("#17A2B8", "white") }
    status_color, text_color = status_map.get(expense['status'], ("#6C757D", "white"))

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{expense['description']}**")
            st.caption(f"By: {submitter['name']} on {expense['submitted_at'].strftime('%d %b, %Y')} | Amount: **₹{expense['amount']:.2f}**")
        with col2:
            st.markdown(f'<div style="background-color: {status_color}; color: {text_color}; padding: 8px; border-radius: 10px; text-align: center;">{expense["status"]}</div>', unsafe_allow_html=True)

        with st.expander("View Details, Approval Chain & Actions"):
            st.image(expense['receipt_url'], caption="Uploaded Receipt")
            st.markdown("---")
            st.subheader("Approval Chain")
            for step in expense.get('approvals', []):
                role_name = step['role'].replace('_', ' ').title()
                if step['approved']:
                    st.success(f"✅ {role_name}: Approved by {step['approved_by']}", icon="✅")
                else:
                    st.warning(f"⏳ {role_name}: Awaiting Approval", icon="⏳")
            
            # --- Role-based Actions ---
            if user['role'] == "team_lead" and expense['status'] == "Pending Team Lead":
                if st.button("Approve (Team Lead)", key=f"approve_{expense['id']}", type="primary"):
                    api.approve_expense_step(expense['id'], user); on_update()
            
            if user['role'] == "treasurer":
                if expense['status'] == "Pending Treasurer":
                    if st.button("Approve (Treasurer)", key=f"approve_{expense['id']}", type="primary"):
                        api.approve_expense_step(expense['id'], user); on_update()
                if expense['status'] == "Approved":
                    if st.button("💸 Mark as Reimbursed", key=f"reimburse_{expense['id']}", type="primary"):
                        api.reimburse_expense(expense['id'], user); on_update()