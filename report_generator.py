# report_generator.py

from fpdf import FPDF
from datetime import datetime
import pandas as pd
import json

class PDF(FPDF):
    # (No changes needed in the PDF class itself)
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'FestFlow AI - Final Financial Report', 0, 1, 'C')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)
    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()
    def add_table(self, df):
        self.set_font('Arial', 'B', 10)
        col_widths = [40, 80, 40]
        for i, col_name in enumerate(df.columns):
            self.cell(col_widths[i], 10, col_name, 1, 0, 'C')
        self.ln()
        self.set_font('Arial', '', 10)
        for index, row in df.iterrows():
            for i, item in enumerate(row):
                self.cell(col_widths[i], 10, str(item), 1)
            self.ln()
        self.ln(10)

def generate_report(event_data, reimbursed_df):
    # This function now receives a DataFrame with ONLY reimbursed expenses
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title('1. Executive Summary')
    total_budget = event_data['budget']
    total_spent = reimbursed_df['amount'].sum() # Use the received df directly
    surplus = total_budget - total_spent
    summary_text = (
        f"Event Name: {event_data['name']}\n"
        f"Report Generated On: {datetime.now().strftime('%d %b %Y')}\n\n"
        f"Total Budget Allotted: INR {total_budget:,.2f}\n"
        f"Total Expenses Reimbursed: INR {total_spent:,.2f}\n"
        f"Final Surplus / Deficit: INR {surplus:,.2f}"
    )
    pdf.chapter_body(summary_text)
    
    pdf.chapter_title('2. Spending by Category')
    category_spend = reimbursed_df.groupby('category')['amount'].sum().reset_index()
    pdf.add_table(category_spend)

    pdf.chapter_title('3. Reimbursed Transaction Log')
    report_table_df = reimbursed_df[['user', 'description', 'amount', 'transaction_id']]
    pdf.set_font('Arial', 'B', 10)
    col_widths = [30, 80, 30, 40]
    for i, col_name in enumerate(report_table_df.columns): 
        pdf.cell(col_widths[i], 10, col_name, 1, 0, 'C')
    pdf.ln()
    pdf.set_font('Arial', '', 9)
    for _, row in report_table_df.iterrows():
        for i, item in enumerate(row): 
            pdf.cell(col_widths[i], 10, str(item), 1)
        pdf.ln()

    return bytes(pdf.output())

def generate_json_report(event_data, reimbursed_df):
    # This function now receives a DataFrame with ONLY reimbursed expenses
    total_spent = reimbursed_df['amount'].sum()
    
    # Create a copy to safely modify
    transactions_df = reimbursed_df.copy()
    
    # Convert datetime to string for JSON compatibility
    transactions_df['reimbursed_at'] = transactions_df['reimbursed_at'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    transactions_list = transactions_df[
        ['user', 'description', 'amount', 'category', 'transaction_id', 'reimbursed_at']
    ].to_dict('records')

    report_data = {
        "event_summary": {
            "event_name": event_data['name'],
            "report_generated_on_utc": datetime.utcnow().isoformat(),
            "total_budget": event_data['budget'],
            "total_reimbursed": float(total_spent),
            "final_surplus_deficit": float(event_data['budget'] - total_spent)
        },
        "spending_by_category": {k: float(v) for k, v in reimbursed_df.groupby('category')['amount'].sum().to_dict().items()},
        "reimbursed_transactions": transactions_list
    }
    
    return json.dumps(report_data, indent=4)