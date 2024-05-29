# This is a steamlit version, try it out
# End Generation Here
import streamlit as st
import datetime
import stripe
import time
import pandas as pd

# Streamlit app to input Stripe API key and generate dashboard
def main():
    st.title("Stripe Metrics Dashboard Generator")
    api_key = st.text_input("Enter your Stripe API key:", type="password")

    if api_key:
        stripe.api_key = api_key
        try:
            monthly_data = generate_dashboard_metrics()
            latest_month_data = {key: values[-1] for key, values in monthly_data.items() if key != 'Month'}
            latest_month = monthly_data['Month'][-1]

            # Display the metrics for the latest month
            st.subheader(f"Metrics for {latest_month}")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric(label="GMV", value=f"${latest_month_data['GMV']:,.2f}")
            with col2:
                st.metric(label="Revenue", value=f"${latest_month_data['Revenue']:,.2f}")
            with col3:
                st.metric(label="Revenue/GMV Ratio", value=f"{(latest_month_data['Revenue'] / latest_month_data['GMV'] * 100):.2f}%")
            with col4:
                st.metric(label="Authorization Rate", value=f"{latest_month_data['Authorization Rate']:.2f}%")
            with col5:
                st.metric(label="Dispute Rate", value=f"{latest_month_data['Dispute Rate']:.2f}%")
            with col5:
                st.metric(label="Fraud Rate", value=f"{latest_month_data['Fraud Rate']:.2f}%")

            # Plotting the data
            df = pd.DataFrame(monthly_data)
            st.subheader("Trend Over the Past 6 Months")
            for metric in ['GMV', 'Revenue', 'Authorization Rate', 'Dispute Rate', 'Fraud Rate']:
                st.line_chart(df.set_index('Month')[metric], height=300, use_container_width=True, title=f"Trend for {metric}")

        except Exception as e:
            st.error(f"Failed to generate dashboard: {str(e)}")
    else:
        st.warning("Please enter a valid Stripe API key to generate the dashboard.")
        
    
def generate_dashboard_metrics():
    # Define the time period for the data (past 6 months)
    today = datetime.date.today()
    last_day_last_month = today.replace(day=1) - datetime.timedelta(days=1)
    first_day_six_months_ago = last_day_last_month - datetime.timedelta(days=180)

    monthly_data = {
        'Month': [],
        'GMV': [],
        'Revenue': [],
        'Authorization Rate': [],
        'Dispute Rate': [],
        'Fraud Rate': []
    }

    for month_start in pd.date_range(start=first_day_six_months_ago, end=last_day_last_month, freq='MS'):
        month_end = (month_start + pd.offsets.MonthEnd(1)).date()
        month_start_unix = int(time.mktime(month_start.timetuple()))
        month_end_unix = int(time.mktime(month_end.timetuple()))

        payment_intents = stripe.PaymentIntent.list(
            created={'gte': month_start_unix, 'lte': month_end_unix}
        )
        disputes = stripe.Dispute.list(
            created={'gte': month_start_unix, 'lte': month_end_unix}
        )

        # Calculate metrics as before
        approved_payments = sum(1 for pi in payment_intents.data if pi['status'] == 'succeeded')
        total_payments = len(set(pi.id for pi in payment_intents.data))
        authorization_rate = (approved_payments / total_payments) * 100 if total_payments > 0 else 0

        disputed_payments = sum(1 for d in disputes.data if d['id'] is not None)
        dispute_rate = (disputed_payments / total_payments) * 100 if total_payments > 0 else 0

        fraudulent_disputes = sum(1 for d in disputes.data if d['id'] is not None and d['reason'] == 'fraudulent')
        fraud_rate = (fraudulent_disputes / total_payments) * 100 if total_payments > 0 else 0

        gmv = sum(pi['amount'] for pi in payment_intents.data)
        refunded_amount = sum(ref['amount'] for ref in disputes.data if ref['status'] in ('succeeded', 'pending'))
        chargeback_amount = sum(dis['amount'] for dis in disputes.data if dis['status'] in ('lost', 'warning_closed'))
        revenue = gmv - refunded_amount - chargeback_amount

        # Store data
        monthly_data['Month'].append(month_start.strftime('%Y-%m'))
        monthly_data['GMV'].append(gmv)
        monthly_data['Revenue'].append(revenue)
        monthly_data['Authorization Rate'].append(authorization_rate)
        monthly_data['Dispute Rate'].append(dispute_rate)
        monthly_data['Fraud Rate'].append(fraud_rate)

    return monthly_data

if __name__ == "__main__":
    main()

