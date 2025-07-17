import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import datetime
import mock_api as api

def predict_future_spending(current_event, current_expenses_df):
    """
    Predicts future spending based on historical data and current trajectory.
    """
    # 1. Get Historical Data from the API
    historical_data_all = api.get_historical_data()
    historical_data = historical_data_all.get("TechFest 2023", [])
    if not historical_data:
        return None, None, 0
        
    hist_df = pd.DataFrame(historical_data, columns=['day', 'cumulative_spend'])
    
    # 2. Train a simple linear regression model on historical data
    model = LinearRegression()
    X_hist = hist_df[['day']]
    y_hist = hist_df['cumulative_spend']
    model.fit(X_hist, y_hist)
    
    # 3. Prepare current event data
    event_start_date_str = api.get_event_by_id(current_event['id'])['start_date']
    event_start_date = datetime.datetime.fromisoformat(event_start_date_str).date()
    
    if not current_expenses_df.empty:
        current_expenses_df['day'] = (current_expenses_df['submitted_at'].dt.date - event_start_date).dt.days + 1
        approved_spend = current_expenses_df[current_expenses_df['status'].isin(['Approved', 'Reimbursed'])]
        daily_cumulative = approved_spend.groupby('day')['amount'].sum().cumsum().reset_index()
    else:
        daily_cumulative = pd.DataFrame(columns=['day', 'amount'])

    # 4. Predict for the next 30 days
    last_day = daily_cumulative['day'].max() if not daily_cumulative.empty else 0
    future_days = np.array(range(int(last_day) + 1, 31)).reshape(-1, 1)
    
    last_known_spend = daily_cumulative['amount'].iloc[-1] if not daily_cumulative.empty else 0
    
    if future_days.size > 0:
        predicted_spend_increase = model.predict(future_days)
        # Make prediction relative to last known point, assuming same slope
        predicted_spend = predicted_spend_increase - model.predict([[last_day]])[0] + last_known_spend
        
        future_df = pd.DataFrame({'day': future_days.flatten(), 'predicted_spend': predicted_spend})
        future_df['predicted_spend'] = future_df['predicted_spend'].clip(lower=last_known_spend)
    else:
        future_df = pd.DataFrame(columns=['day', 'predicted_spend'])
        
    projected_total = future_df['predicted_spend'].iloc[-1] if not future_df.empty else last_known_spend
    
    return daily_cumulative, future_df, projected_total