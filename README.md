# festflwai

# FestFlow AI Pro: Advanced Expense Management

FestFlow AI Pro is a comprehensive Streamlit web application designed to streamline expense management for college festivals and events. It provides a multi-user, role-based system with an automated approval workflow, OCR receipt scanning, and robust financial reporting.

 <!-- You can create a GIF of your app and replace this link -->

---

## ✨ Key Features

*   **🔒 Role-Based Access Control:** A secure login system with three distinct user roles:
    *   **Student:** Can submit new expense claims.
    *   **Team Lead:** Can approve or reject expenses submitted by students.
    *   **Treasurer:** Manages the final approval, oversees the entire budget, and processes reimbursements.
*   **🤖 OCR-Powered Expense Submission:** Students can upload a receipt image, and the application uses Tesseract OCR to automatically extract the expense amount, simplifying the submission process.
*   **🚦 Multi-Level Approval Workflow:** Expenses flow logically from student submission to Team Lead approval, and finally to Treasurer approval before reimbursement.
*   **📊 Interactive Financial Dashboard:** The Treasurer has access to a real-time dashboard with key performance indicators (KPIs) like total budget, amount spent, and remaining funds. It includes interactive charts from Plotly to visualize:
    *   Spending by category.
    *   Cumulative spending over time.
    *   Top spenders.
    *   Overall expense status distribution.
*   **📄 Dual-Format Report Generation:** The Treasurer can generate a final, consolidated financial report in two formats:
    *   **PDF:** A formal, human-readable report for official documentation.
    *   **JSON:** A structured, machine-readable format perfect for data analysis or integration with other systems.
*   **✍️ Complete Activity Log:** An immutable audit trail that logs every significant action taken within the system, providing transparency and accountability.

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
