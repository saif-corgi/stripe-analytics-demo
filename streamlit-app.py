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
            monthly_data, weekly_data = generate_dashboard_metrics()
            latest_month_data = monthly_data.iloc[-1]

            # Display the metrics for the latest month
            st.subheader(f"Metrics for the month ending on {latest_month_data['Date']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="GMV", value=f"${latest_month_data['GMV']:,.2f}")
            with col2:
                st.metric(label="Revenue", value=f"${latest_month_data['Revenue']:,.2f}")
            with col3:
                st.metric(label="Revenue/GMV Ratio", value=f"{(latest_month_data['Revenue'] / latest_month_data['GMV'] * 100):.2f}%")
            
            # Additional metrics for the latest month
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(label="Authorization Rate", value=f"{latest_month_data['Authorization Rate']:.2f}%")
            with col5:
                st.metric(label="Dispute Rate", value=f"{latest_month_data['Dispute Rate']:.2f}%")
            with col6:
                st.metric(label="Fraud Rate", value=f"{latest_month_data['Fraud Rate']:.2f}%")
            
            # Plotting the data
            st.subheader("Monthly Trends Over the Past 6 Months")
            metrics_to_plot = ['GMV', 'Revenue', 'Revenue/GMV Ratio', 'Authorization Rate', 'Dispute Rate', 'Fraud Rate']
            col1, col2 = st.columns(2)
            for i, metric in enumerate(metrics_to_plot):
                chart_data = monthly_data.set_index('Date')[metric]
                with col1 if i % 2 == 0 else col2:
                    st.markdown(f"**{metric}**", unsafe_allow_html=True)
                    if metric in ['GMV', 'Revenue']:
                        st.bar_chart(chart_data, height=300, use_container_width=True)
                    elif metric == 'Revenue/GMV Ratio':
                        st.line_chart((monthly_data['Revenue'] / monthly_data['GMV'] * 100), height=300, use_container_width=True)
                    else:
                        st.line_chart(chart_data, height=300, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to generate dashboard: {str(e)}")
    else:
        st.warning("Please enter a valid Stripe API key to generate the dashboard.")
        
    
def generate_dashboard_metrics():
    # Define the time period for the data (past 6 months)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=180)

    # Initialize an empty list to store weekly and monthly data dictionaries
    weekly_data_list = []
    monthly_data_list = []

    for week_start in pd.date_range(start=start_date, end=today, freq='W-SUN'):
        week_end = week_start + datetime.timedelta(days=6)
        month_end = week_start + datetime.timedelta(days=30)
        week_start_unix = int(time.mktime(week_start.timetuple()))
        week_end_unix = int(time.mktime(week_end.timetuple()))
        month_end_unix = int(time.mktime(month_end.timetuple()))

        payment_intents = stripe.PaymentIntent.list(
            created={'gte': week_start_unix, 'lte': week_end_unix}
        )
        disputes = stripe.Dispute.list(
            created={'gte': week_start_unix, 'lte': week_end_unix}
        )

        # Calculate metrics for the week
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

        # Append weekly data to the list
        weekly_data_list.append({
            'Date': week_end.strftime('%Y-%m-%d'),
            'GMV': gmv,
            'Revenue': revenue,
            'Revenue/GMV Ratio': (revenue / gmv * 100) if gmv > 0 else 0,
            'Authorization Rate': authorization_rate,
            'Dispute Rate': dispute_rate,
            'Fraud Rate': fraud_rate
        })

        # Append monthly data to the list
        if week_end.day >= 28:  # Assuming the last week of the month captures the monthly data
            monthly_data_list.append({
                'Date': month_end.strftime('%Y-%m-%d'),
                'GMV': gmv,
                'Revenue': revenue,
                'Revenue/GMV Ratio': (revenue / gmv * 100) if gmv > 0 else 0,
                'Authorization Rate': authorization_rate,
                'Dispute Rate': dispute_rate,
                'Fraud Rate': fraud_rate
            })

    # Convert list of dictionaries to DataFrame
    weekly_data = pd.DataFrame(weekly_data_list)
    monthly_data = pd.DataFrame(monthly_data_list)

    return monthly_data, weekly_data

if __name__ == "__main__":
    main()
