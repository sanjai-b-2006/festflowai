import streamlit as st
import os
import mock_api as api
import datetime

def status_chip(status):
    color_map = {
        "Pending":              ("#fe9500", "#181c25"),
        "Pending Team Lead":    ("#fe9500", "#181c25"),
        "Pending Treasurer":    ("#fe9500", "#181c25"),
        "Approved":             ("#21a475", "#fff"),
        "Approved by Team Lead":("#21a475", "#fff"),
        "Paid":                 ("#156fa6", "#fff"),
        "Rejected":             ("#eb3941", "#fff"),
        "Closed":               ("#6135bb", "#fff"),
        "Reimbursed":           ("#2290e3", "#fff"),
        "Unknown":              ("#2c2e3c", "#fff")
    }
    bg, fg = color_map.get(status, ("#2c2e3c", "#fff"))
    return (f"<span style='background-color:{bg};color:{fg};"
            f"padding:6px 18px;border-radius:999px;font-weight:700;"
            f"font-size:1.01em;letter-spacing:0.01em;margin-left:8px;'>{status}</span>")

def render_expense_card(expense, user, on_update):
    import datetime
    submitter = api.get_user_details(expense['user'])
    status = expense.get('status', 'Unknown')

    with st.container(border=True):
        col_left, col_center, col_right = st.columns([4, 2, 2])

        # LEFT: Main details and receipt preview
        with col_left:
            st.markdown(f"**{expense.get('description', '')}**")
            st.caption(f"By: {submitter['name']} — {expense['submitted_at'].strftime('%d-%b-%Y')}")
            st.caption(f"Category: {expense.get('category', 'Uncategorized')}")
            if expense.get("receipt_url") and os.path.exists(expense["receipt_url"]):
                with st.expander("🧾 Preview Receipt"):
                    st.image(expense["receipt_url"], use_column_width=True)

        # CENTER: Amount and Status Chips
        with col_center:
            st.metric("Amount", f"₹{expense.get('amount',0):.2f}")
            st.markdown(status_chip(status), unsafe_allow_html=True)

        # RIGHT: Approval/Reimbursement Buttons (only if actionable)
        with col_right:
            # Determine if this user can approve/reject
            show_approval = any(step['role'] == user['role'] and not step['approved'] for step in expense.get('approvals', []))
            if show_approval and status.startswith("Pending"):
                with st.form(key=f"form_exp_{expense['id']}"):
                    a_col, r_col = st.columns(2)
                    approve_btn = a_col.form_submit_button("✅ Approve")
                    reject_btn = r_col.form_submit_button("❌ Reject")
                    comment = st.text_input("Reason for rejection (required)", key=f"reject_reason_{expense['id']}")
                    if approve_btn:
                        api.approve_expense_step(expense['id'], user)
                        st.success("Approved.")
                        on_update()
                    elif reject_btn:
                        if not comment.strip():
                            st.warning("You must provide a reason to reject.")
                        else:
                            api.add_comment_to_expense(expense['id'], user, comment.strip())
                            expense['status'] = "Rejected"
                            api.save_data(api.EXPENSES_FILE, api.load_data(api.EXPENSES_FILE))
                            api.log_activity(user['name'], f"rejected expense #{expense['id']}")
                            st.warning("Rejected.")
                            on_update()

            # Treasurer reimbursement form, only if actionable
            if status == 'Approved' and user['role'] == 'treasurer':
                upi_id = submitter.get('upi_id', '')
                if not upi_id:
                    st.error("No UPI ID provided. Ask student to update UPI ID before reimbursing.")
                else:
                    with st.form(key=f"reimburse_form_{expense['id']}"):
                        txn_id = st.text_input("Transaction ID or UPI Reference", key=f"txn_{expense['id']}")
                        submit = st.form_submit_button("💸 Reimburse")
                        if submit:
                            if not txn_id:
                                st.warning("Transaction ID is required to mark reimbursement.")
                            else:
                                success = api.reimburse_expense(expense['id'], user, txn_id)
                                if success:
                                    st.success("Expense marked as reimbursed.")
                                    on_update()
                                else:
                                    st.error("Failed to reimburse. Please ensure the expense is valid.")

        # COMMENTS always visible, always for this expense!
        with st.expander("💬 Comments", expanded=False):
            comment_input = st.text_input(f"Add a comment for expense #{expense['id']}", key=f"cmt_exp_{expense['id']}")
            if st.button("Post Comment", key=f"btn_cmt_exp_{expense['id']}"):
                if comment_input.strip():
                    api.add_comment_to_expense(expense['id'], user, comment_input.strip())
                    st.success("Comment added.")
                    on_update()
                else:
                    st.warning("Comment cannot be empty.")
            comments = expense.get("comments", [])
            if comments:
                for comment in comments:
                    ts = comment['timestamp'].strftime('%d-%b %I:%M %p') if isinstance(comment['timestamp'], datetime.datetime) else str(comment['timestamp'])
                    st.caption(f"- {comment['user']} ({comment['role']}, {ts}): {comment['text']}")
            else:
                st.caption("No comments yet. Add one above!")


def render_advance_card(advance, show_actions=False, user=None, on_update=None):
    import datetime
    status = advance.get('status', 'Unknown')
    if on_update is None:
        on_update = lambda: None

    with st.container(border=True):
        col1, col2, col3 = st.columns([4,2,2])

        # LEFT: Vendor/purpose/etc
        with col1:
            st.markdown(f"**Vendor:** {advance.get('vendor','')}")
            st.caption(advance.get('purpose',''))
            st.caption(f"Requested by: {advance.get('user','')}")
            if advance.get("approved_by"):
                st.caption(f"Approved by: {advance['approved_by']}")
            if advance.get("paid_by"):
                st.caption(f"Paid by: {advance.get('paid_by')}")
            if advance.get('quote_url') and os.path.exists(advance['quote_url']):
                with st.expander("🧾 Preview Vendor Quote"):
                    st.image(advance['quote_url'], use_column_width=True)
            if advance.get('receipt_url') and os.path.exists(advance['receipt_url']):
                with st.expander("🧾 Preview Final Receipt"):
                    st.image(advance['receipt_url'], use_column_width=True)

        # CENTER: Amount/status chip
        with col2:
            st.metric("Amount", f"₹{advance.get('amount',0):.2f}")
            st.markdown(status_chip(status), unsafe_allow_html=True)
            if advance.get("paid_txn_id"):
                st.caption(f"Transaction ID: {advance['paid_txn_id']}")

        # RIGHT: Approve/Reject/Pay
        with col3:
            # ---- Approve/Reject via Form ----
            if show_actions and user and on_update:
                if user['role'] == "team_lead" and status == "Pending":
                    with st.form(key=f"form_adv_{advance['id']}"):
                        a_col, r_col = st.columns(2)
                        approve_btn = a_col.form_submit_button("✅ Approve")
                        reject_btn = r_col.form_submit_button("❌ Reject")
                        comment = st.text_input("Reason for rejection (required)", key=f"reject_comment_{advance['id']}")
                        msg = ""
                        if approve_btn:
                            advance['status'] = "Approved by Team Lead"
                            advance['approved_by'] = user['name']
                            api.save_data("db_advances.json", api.load_data("db_advances.json"))
                            api.log_activity(user['name'], f"approved advance #{advance['id']}")
                            st.success("Approved.")
                            on_update()
                        elif reject_btn:
                            if not comment.strip():
                                st.warning("You must provide a reason to reject.")
                            else:
                                advance['status'] = "Rejected"
                                api.add_comment_to_advance(advance['id'], user, comment.strip())
                                api.save_data("db_advances.json", api.load_data("db_advances.json"))
                                api.log_activity(user['name'], f"rejected advance #{advance['id']}")
                                st.warning("Rejected.")
                                on_update()
                elif user['role'] == "treasurer" and status == "Approved by Team Lead":
                    txn_col, btn_col = st.columns([3, 1])
                    txn_id = txn_col.text_input("Transaction ID / Reference", key=f"txn_adv_{advance['id']}")
                    if btn_col.button("💸 Mark as Paid", key=f"pay{advance['id']}"):
                        if not txn_id.strip():
                            st.warning("Please provide a transaction ID.")
                        else:
                            advance['status'] = "Paid"
                            advance['paid_txn_id'] = txn_id.strip()
                            advance['paid_time'] = datetime.datetime.now().isoformat()
                            advance['paid_by'] = user['name']
                            api.save_data("db_advances.json", api.load_data("db_advances.json"))
                            api.log_activity(user['name'], f"marked advance #{advance['id']} as paid (txn: {txn_id})")
                            st.success("Marked as Paid.")
                            on_update()

            # ---- Comments Section ----
            user = st.session_state.get("user_info")
            with st.expander("💬 Comments", expanded=False):
                comment_input = st.text_input(f"Add a comment for advance #{advance['id']}", key=f"cmt_adv_{advance['id']}")
                if st.button("Post Comment", key=f"btn_cmt_adv_{advance['id']}"):
                    if user is None:
                        st.error("⚠️ Logged-in user not found. Cannot add comment.")
                    elif comment_input.strip():
                        api.add_comment_to_advance(advance['id'], user, comment_input.strip())
                        st.success("Comment added.")
                        on_update()
                    else:
                        st.warning("Comment cannot be empty.")

                comments = advance.get("comments", [])
                if isinstance(comments, list) and comments:
                    for comment in comments:
                        ts = comment['timestamp'].strftime('%d-%b %I:%M %p') if isinstance(comment['timestamp'], datetime.datetime) else str(comment['timestamp'])
                        st.caption(f"- {comment['user']} ({comment['role']}, {ts}): {comment['text']}")
                else:
                    st.caption("No comments yet. Add one above!")




