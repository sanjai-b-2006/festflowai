import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import datetime
import mock_api as api
import plotly.graph_objects as go

def generate_forecast_chart(current_event, current_expenses_df):
    """
    Generates a Plotly chart with current, predicted, and historical spending.
    This function now expects a DataFrame with a clean, pre-validated 'submitted_at' column.
    """

    historical_data_all = api.get_historical_data()
    historical_data = historical_data_all.get("TechFest 2023", [])

    if not historical_data:
        hist_df = pd.DataFrame(columns=['day', 'cumulative_spend'])
    else:
        hist_df = pd.DataFrame(historical_data, columns=['day', 'cumulative_spend'])

    projected_total = 0
    future_df = pd.DataFrame(columns=['day', 'predicted_spend'])

    if not hist_df.empty:
        model = LinearRegression()
        X_hist = hist_df[['day']]
        y_hist = hist_df['cumulative_spend']
        model.fit(X_hist, y_hist)

    # Convert event start date
    event_start_date_str = api.get_event_by_id(current_event['id'])['start_date']
    event_start_date = datetime.datetime.fromisoformat(event_start_date_str).date()

    if not current_expenses_df.empty:
        # ✅ FIXED: Compute day difference correctly
        current_expenses_df['day'] = (
            current_expenses_df['submitted_at'].dt.date.apply(lambda d: (d - event_start_date).days + 1)
        )

        approved_spend = current_expenses_df[current_expenses_df['status'].isin(['Approved', 'Reimbursed'])]

        if not approved_spend.empty:
            daily_cumulative = (
                approved_spend.sort_values('day')
                .groupby('day')['amount']
                .sum()
                .cumsum()
                .reset_index()
            )
            daily_cumulative.rename(columns={'amount': 'cumulative_spend'}, inplace=True)
        else:
            daily_cumulative = pd.DataFrame(columns=['day', 'cumulative_spend'])
    else:
        daily_cumulative = pd.DataFrame(columns=['day', 'cumulative_spend'])

    # Predict future values
    last_day = daily_cumulative['day'].max() if not daily_cumulative.empty else 0
    future_days = np.array(range(int(last_day) + 1, 31)).reshape(-1, 1)

    last_known_spend = daily_cumulative['cumulative_spend'].iloc[-1] if not daily_cumulative.empty else 0

    if not hist_df.empty and future_days.size > 0:
        predicted_spend_increase = model.predict(future_days)
        last_day_prediction_base = model.predict([[last_day]])[0] if last_day > 0 else 0
        predicted_spend = predicted_spend_increase - last_day_prediction_base + last_known_spend

        future_df = pd.DataFrame({'day': future_days.flatten(), 'predicted_spend': predicted_spend})
        future_df['predicted_spend'] = future_df['predicted_spend'].clip(lower=last_known_spend)
    else:
        future_df = pd.DataFrame(columns=['day', 'predicted_spend'])

    projected_total = (
        future_df['predicted_spend'].iloc[-1] if not future_df.empty else last_known_spend
    )

    # Create chart
    fig = go.Figure()

    if not daily_cumulative.empty:
        fig.add_trace(go.Scatter(
            x=daily_cumulative['day'], y=daily_cumulative['cumulative_spend'],
            mode='lines+markers', name=f'{current_event["name"]} (Actual)',
            line=dict(color='royalblue', width=3)
        ))

    if not future_df.empty:
        fig.add_trace(go.Scatter(
            x=future_df['day'], y=future_df['predicted_spend'],
            mode='lines', name='Forecast',
            line=dict(color='firebrick', width=2, dash='dash')
        ))

    if not hist_df.empty:
        fig.add_trace(go.Scatter(
            x=hist_df['day'], y=hist_df['cumulative_spend'],
            mode='lines', name='TechFest 2023 (Historical)',
            line=dict(color='grey', width=2, dash='dot')
        ))

    fig.update_layout(
        title="Spending Trajectory: Actual vs. Forecast vs. Historical",
        xaxis_title="Days Since Event Start",
        yaxis_title="Cumulative Spend (₹)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig, projected_total
