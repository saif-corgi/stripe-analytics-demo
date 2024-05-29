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
            rolling_data = generate_dashboard_metrics()
            latest_data = {key: values[-1] for key, values in rolling_data.items() if key != 'Date'}
            latest_date = rolling_data['Date'][-1]

            # Display the metrics for the latest date
            st.subheader(f"Metrics for {latest_date}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="GMV", value=f"${latest_data['GMV']:,.2f}")
            with col2:
                st.metric(label="Revenue", value=f"${latest_data['Revenue']:,.2f}")
            with col3:
                st.metric(label="Revenue/GMV Ratio", value=f"{(latest_data['Revenue'] / latest_data['GMV'] * 100):.2f}%")
            
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(label="Authorization Rate", value=f"{latest_data['Authorization Rate']:.2f}%")
            with col5:
                st.metric(label="Dispute Rate", value=f"{latest_data['Dispute Rate']:.2f}%")
            with col6:
                st.metric(label="Fraud Rate", value=f"{latest_data['Fraud Rate']:.2f}%")

            # Plotting the data
            df = pd.DataFrame(rolling_data)
            st.subheader("Trend Over the Past 6 Months")
            metrics_to_plot = ['GMV', 'Revenue', 'Authorization Rate', 'Dispute Rate', 'Fraud Rate']
            for i in range(0, len(metrics_to_plot), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(metrics_to_plot):
                        metric = metrics_to_plot[i + j]
                        with cols[j]:
                            chart = st.line_chart(df.set_index('Date')[metric], height=300, use_container_width=True)
                            chart.pyplot.xlabel('Date')
                            chart.pyplot.ylabel(metric)
                            st.caption(metric)

        except Exception as e:
            st.error(f"Failed to generate dashboard: {str(e)}")
    else:
        st.warning("Please enter a valid Stripe API key to generate the dashboard.")
        
    
def generate_dashboard_metrics():
    # Define the time period for the data (past 6 months)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=180)

    rolling_data = {
        'Date': [],
        'GMV': [],
        'Revenue': [],
        'Authorization Rate': [],
        'Dispute Rate': [],
        'Fraud Rate': []
    }

    for day in pd.date_range(start=start_date, end=today, freq='D'):
        day_end = day + datetime.timedelta(days=13)  # 14 days including the start day
        day_start_unix = int(time.mktime(day.timetuple()))
        day_end_unix = int(time.mktime(day_end.timetuple()))

        payment_intents = stripe.PaymentIntent.list(
            created={'gte': day_start_unix, 'lte': day_end_unix}
        )
        disputes = stripe.Dispute.list(
            created={'gte': day_start_unix, 'lte': day_end_unix}
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
        rolling_data['Date'].append(day.strftime('%Y-%m-%d'))
        rolling_data['GMV'].append(gmv)
        rolling_data['Revenue'].append(revenue)
        rolling_data['Authorization Rate'].append(authorization_rate)
        rolling_data['Dispute Rate'].append(dispute_rate)
        rolling_data['Fraud Rate'].append(fraud_rate)

    return rolling_data

if __name__ == "__main__":
    main()

