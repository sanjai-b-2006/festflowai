# festflwai

# FestFlow AI Pro: Advanced Expense Management

FestFlow AI Pro is a comprehensive Streamlit web application designed to streamline expense management for college festivals and events. It provides a multi-user, role-based system with an automated approval workflow, OCR receipt scanning, and robust financial reporting.

 <!-- You can create a GIF of your app and replace this link -->

---

# FestFlow AI Pro: Project Features Overview


## 1. Expense Management

- **Expense Submission**  
  - Users can submit expenses by uploading receipts and providing details like category, amount, and description.
  - OCR integration allows automatic extraction of amounts from uploaded receipts for convenience.
- **Expense Approval Workflow**  
  - Team leads and treasurers can view, approve, or reject expense requests with required rejection comments.
  - Each step is logged, and comments are visible in a conversation-style expander on each card.
- **Expense Reimbursement**  
  - Treasurers can mark approved expenses as reimbursed, entering a transaction/UPI reference.
  - Keeps an audit log of all reimbursements.
- **Commenting System**  
  - Comments can be added to any expense at any stage.
  - All comments show the commenter’s name, role, timestamp, and message.

## 2. Advance Management

- **Advance Request Submission**  
  - Users can request advances for specific vendors and purposes, optionally uploading a vendor quote.
- **Advance Approval Workflow**  
  - Team leads can approve or reject advances (rejection requires a reason/comment).
  - Treasurers can mark advances as “Paid” with a transaction ID.
  - Advances are closed when the requester uploads a final receipt after spending.
- **Inline Document Preview**  
  - Both vendor quotes and final receipts can be previewed directly in the card UI via expanders.
- **Comments & Audit Trail**  
  - Anyone with access can add comments to advances at any stage.
  - All actions and comments are tracked with full attribution.

## 3. Personalized User Dashboard

- **Role-Based Navigation**  
  - Students, team leads, and treasurers see menu options appropriate to their roles.
  - Quick access to pending actions and personalized lists.
- **Dynamic Action Badges**  
  - Pending approvals/actions are highlighted prominently in the navigation.

## 4. Approval & History Tracking

- **Manage Approvals**  
  - Approvers have a dashboard displaying all requests requiring their immediate action (both expenses and advances).
  - Once processed, requests move out of the action queue and appear in the appropriate “My Approvals” or history listing.
- **My Approvals (History)**  
  - Approvers can see all expenses and advances they’ve acted upon, including status and all associated comments.

## 5. Data Visualization & Reporting

- **Dashboard Analytics**  
  - View event spending with real-time and historical graphs (uses Plotly).
  - Compare current, forecasted, and historical spending patterns.
- **PDF & JSON Report Generation**  
  - Generate final financial reports of the event, including expense log, category-wise summary, and surplus/deficit figures.
  - Reports are available as PDF and JSON.
- **Activity Log**  
  - Comprehensive log of all significant activities for full transparency and audit.

## 6. UPI ID Management

- **Edit UPI ID**  
  - Students can add and edit their UPI IDs for reimbursement purposes.

## 7. Smart Features & Automation

- **OCR-Driven Amount Extraction**  
  - Automated recognition of key totals from uploaded receipts (using Tesseract OCR).
- **Automatic State Transitions**  
  - Cards update status and move automatically between “Pending”, “Approved”, “Paid”, and “Closed” as actions are completed.

## 8. Modern, Responsive UI

- **Three-Column Card Layout**  
  - All requests (expenses and advances) are shown in a modern, visually unified format with colored status chips, inline file previews, and comments.
- **Always-On Comment Expanders**  
  - Every card features a comments expander where ongoing discussion or rejection reasons appear.
- **User Feedback**  
  - Success and warning messages display instantly for all major actions.

---

## ⚙️ Technology Stack

*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **Data Manipulation:** [Pandas](https://pandas.pydata.org/)
*   **Data Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/)
*   **OCR:** [Pytesseract](https://pypi.org/project/pytesseract/)
*   **PDF Generation:** [fpdf2](https://pypi.org/project/fpdf2/)

*   <img width="1522" height="955" alt="Screenshot 2025-07-17 224622" src="https://github.com/user-attachments/assets/c952ef5e-c057-4a30-bfc8-cec66e70334a" />


*   <img width="725" height="800" alt="Screenshot 2025-07-17 224708" src="https://github.com/user-attachments/assets/01ada79b-b3da-444f-9006-06d30347f137" />

*   **Backend Simulation:** JSON files acting as a mock database.

---

## 🚀 How to Run the Application

Follow these steps to set up and run the project on your local machine.

### **Prerequisites**

1.  **Python:** Make sure you have Python 3.8 or newer installed.
2.  **Tesseract-OCR Engine:** This is a system dependency, **not** a Python package. You must install it on your operating system.
    *   **Windows:** Download and run the installer from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). During installation, make sure to add it to your system's PATH.
    *   **macOS:** Use Homebrew: `brew install tesseract`
    *   **Linux (Ubuntu/Debian):** `sudo apt-get install tesseract-ocr`

    _**Note for Windows Users:**_ The file `ocr_processor.py` contains a line `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`. Ensure this path matches your Tesseract installation location.

### **Step 1: Get the Code**

Download or clone the project files to a folder on your computer.

### **Step 2: Create a Virtual Environment**

Open your terminal or command prompt, navigate into the project folder, and create a virtual environment. This isolates the project's dependencies.

```bash
# Navigate to your project folder
cd path/to/your/festflow-ai

# Create a virtual environment named 'venv'
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
