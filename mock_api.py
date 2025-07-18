import json
import os
import datetime

# --- File Paths for our JSON 'Database' ---
USERS_FILE = 'db_users.json'
EVENTS_FILE = 'db_events.json'
EXPENSES_FILE = 'db_expenses.json'
LOG_FILE = 'db_activity_log.json'
HISTORICAL_FILE = 'db_historical.json'

# --- Datetime Handling for JSON ---
def json_default_converter(o):
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()

def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return data

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, default=json_default_converter)

def add_advance_request(user, event_id, vendor, purpose, amount, quote_file):
    advances = load_data("db_advances.json")
    quote_url = ''
    if quote_file:
        if not os.path.exists("uploads"): os.makedirs("uploads")
        quote_url = os.path.join("uploads", f"{int(datetime.datetime.now().timestamp())}_{quote_file.name}")
        with open(quote_url, "wb") as f:
            f.write(quote_file.getbuffer())

    new = {
        "id": advances[-1]['id'] + 1 if advances else 1,
        "user": user['username'],
        "event_id": event_id,
        "vendor": vendor,
        "purpose": purpose,
        "amount": amount,
        "quote_url": quote_url,
        "status": "Pending",
        "submitted_at": datetime.datetime.now(),
        "receipt_url": None,
        "comments": []
    }
    
    advances.append(new)
    save_data("db_advances.json", advances)
    log_activity(user['name'], f"requested advance of ₹{amount:.2f} for {vendor}")
    return new

def get_advances_for_user(username):
    return [a for a in parse_datetimes(load_data("db_advances.json")) if a['user'] == username]

def close_advance(adv_id, user, receipt_file):
    advances = load_data("db_advances.json")
    for adv in advances:
        if adv['id'] == adv_id:
            receipt_path = os.path.join("uploads", f"{int(datetime.datetime.now().timestamp())}_{receipt_file.name}")
            with open(receipt_path, "wb") as f:
                f.write(receipt_file.getbuffer())
            adv['receipt_url'] = receipt_path
            adv['status'] = "Closed"
            log_activity(user['name'], f"closed advance #{adv_id}")
            break
    save_data("db_advances.json", advances)

def setup_database():
    """Creates the JSON database files with default data if they don't exist."""
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        save_data(USERS_FILE, [
            {"username": "treasurer", "password": "pw", "name": "Sanjai", "role": "treasurer"},
            {"username": "team_lead", "password": "pw", "name": "Ronaldo", "role": "team_lead"},
            {"username": "student1", "password": "pw", "name": "Siuuu", "role": "student", "upi_id": "Siuuu@okhdfcbank"},
            {"username": "student2", "password": "pw", "name": "Pessi", "role": "student", "upi_id": "Pessi@okhdfcbank"},
            {"username": "student3", "password": "pw", "name": "Carter", "role": "student", "upi_id": ""}
        ])
    if not os.path.exists(EVENTS_FILE):
        save_data(EVENTS_FILE, [{"id": 1, "name": "TechFest 2024", "budget": 50000, "start_date": "2024-04-01"}])
    if not os.path.exists(EXPENSES_FILE):
        save_data(EXPENSES_FILE, [])
    if not os.path.exists(LOG_FILE):
        save_data(LOG_FILE, [{'timestamp': datetime.datetime.now(), 'user': 'System', 'action': 'Database initialized.'}])
    if not os.path.exists(HISTORICAL_FILE):
        save_data(HISTORICAL_FILE, {
            "TechFest 2023": [(1, 500), (2, 800), (3, 1200), (5, 1500), (7, 2500), (10, 4000), (12, 6000), (14, 8500),
            (15, 10000), (18, 15000), (20, 22000), (22, 28000), (25, 35000), (28, 41000), (30, 44000)]
        })

def parse_datetimes(data_list, date_keys=['submitted_at', 'reimbursed_at', 'timestamp']):
    """Converts date strings in a list of dicts back to datetime objects."""
    if not data_list:
        return []
    for item in data_list:
        for key in date_keys:
            if item.get(key) and isinstance(item.get(key), str):
                try:
                    item[key] = datetime.datetime.fromisoformat(item[key])
                except (ValueError, TypeError):
                    item[key] = None
        if 'comments' in item:
            for comment in item.get('comments', []):
                if comment.get('timestamp') and isinstance(comment.get('timestamp'), str):
                    try:
                        comment['timestamp'] = datetime.datetime.fromisoformat(comment['timestamp'])
                    except (ValueError, TypeError):
                        comment['timestamp'] = None
    return data_list

# --- Core API Functions ---
def log_activity(user_name, action):
    logs = load_data(LOG_FILE)
    logs.insert(0, {'timestamp': datetime.datetime.now(), 'user': user_name, 'action': action})
    save_data(LOG_FILE, logs)

def add_comment_to_advance(advance_id, user, comment_text):
    advances = load_data("db_advances.json")
    for adv in advances:
        if adv['id'] == advance_id:
            new_comment = {
                "user": user['name'],
                "role": user['role'],
                "text": comment_text,
                "timestamp": datetime.datetime.now()
            }
            adv.setdefault('comments', []).append(new_comment)
            save_data("db_advances.json", advances)
            log_activity(user['name'], f"commented on advance #{advance_id}: '{comment_text}'")
            return True
    return False


def get_activity_log():
    return parse_datetimes(load_data(LOG_FILE))

def authenticate_user(username, password):
    users = load_data(USERS_FILE)
    return next((user for user in users if user['username'] == username and user['password'] == password), None)

def get_user_details(username):
    return next((user for user in load_data(USERS_FILE) if user['username'] == username), None)

def get_all_usernames():
    users = load_data(USERS_FILE)
    return [user['username'] for user in users] if users else []

def get_events_for_user(user):
    return load_data(EVENTS_FILE)

def get_event_by_id(event_id):
    return next((e for e in load_data(EVENTS_FILE) if e['id'] == event_id), None)

def get_historical_data():
    return load_data(HISTORICAL_FILE)

def get_expenses_for_user(username):
    all_expenses = load_data(EXPENSES_FILE)
    user_expenses = list(filter(lambda e: e.get('user') == username, all_expenses))
    return parse_datetimes(user_expenses)

def get_pending_requests(user_role):
    all_expenses = load_data(EXPENSES_FILE)
    pending_expenses = []
    if user_role == "team_lead":
        pending_expenses = [e for e in all_expenses if e.get('status') == 'Pending Team Lead']
    if user_role == "treasurer":
        pending_expenses = [e for e in all_expenses if e.get('status') in ['Pending Treasurer', 'Approved']]
    return parse_datetimes(pending_expenses)

def add_expense(event_id, user, amount, category, description, receipt_file):
    expenses = load_data(EXPENSES_FILE)
    if not os.path.exists("uploads"): os.makedirs("uploads")
    receipt_url = os.path.join("uploads", f"{int(datetime.datetime.now().timestamp())}_{receipt_file.name}")
    with open(receipt_url, "wb") as f: f.write(receipt_file.getbuffer())
    new_expense = {
        "id": (expenses[-1]['id'] + 1) if expenses else 1, "event_id": event_id, "user": user['username'],
        "amount": amount, "category": category, "description": description, "submitted_at": datetime.datetime.now(),
        "receipt_url": receipt_url, "status": "Pending Team Lead",
        "approvals": [{"role": "team_lead", "approved": False, "approved_by": None, "timestamp": None},
                      {"role": "treasurer", "approved": False, "approved_by": None, "timestamp": None}],
        "comments": []
    }
    expenses.append(new_expense)
    save_data(EXPENSES_FILE, expenses)
    log_activity(user['name'], f"submitted an expense of ₹{amount} for '{description}'.")
    return new_expense

def add_comment_to_expense(expense_id, user, comment_text):
    expenses = load_data(EXPENSES_FILE)
    for expense in expenses:
        if expense['id'] == expense_id:
            new_comment = {
                "user": user['name'],
                "role": user['role'],
                "text": comment_text,
                "timestamp": datetime.datetime.now()
            }
            expense.setdefault('comments', []).append(new_comment)
            save_data(EXPENSES_FILE, expenses)
            log_activity(user['name'], f"commented on expense #{expense_id}: '{comment_text}'")
            return True
    return False

def approve_expense_step(expense_id, approver_user):
    expenses = load_data(EXPENSES_FILE)
    for expense in expenses:
        if expense['id'] == expense_id:
            for i, step in enumerate(expense['approvals']):
                if step['role'] == approver_user['role'] and not step['approved']:
                    step['approved'], step['approved_by'], step['timestamp'] = True, approver_user['name'], datetime.datetime.now()
                    if i + 1 < len(expense['approvals']):
                        next_step_role = expense['approvals'][i+1]['role']
                        expense['status'] = f"Pending {next_step_role.replace('_', ' ').title()}"
                    else:
                        expense['status'] = "Approved"
                    log_activity(approver_user['name'], f"approved expense #{expense_id} at the {approver_user['role']} level.")
                    save_data(EXPENSES_FILE, expenses)
                    return True
    return False

def reimburse_expense(expense_id, approver_user, transaction_id):
    expenses = load_data(EXPENSES_FILE)
    for expense in expenses:
        if expense['id'] == expense_id and expense['status'] == 'Approved':
            expense['status'] = 'Reimbursed'
            expense['reimbursed_at'] = datetime.datetime.now()
            expense['transaction_id'] = transaction_id  # Use the transaction ID entered by treasurer
            save_data(EXPENSES_FILE, expenses)
            submitter_details = get_user_details(expense['user'])
            upi_id = submitter_details.get('upi_id', 'N/A')
            log_message = f"reimbursed expense #{expense_id} (₹{expense['amount']}) via UPI to {submitter_details['name']} ({upi_id}). Transaction ID: {transaction_id}"
            log_activity(approver_user['name'], log_message)
            return True
    return False
