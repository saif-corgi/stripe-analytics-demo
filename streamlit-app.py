import streamlit as st
import datetime
import stripe
import time
import pandas as pd
import plotly.express as px
# To center the logo, you can use Streamlit's columns to center the image.
# First, ensure your image is hosted and publicly accessible, as previously described.

# Example using a direct link from Google Drive:
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("https://github.com/saif-corgi/stripe-analytics-demo/blob/main/CorgiAI%20logo%20(dark%20background).png?raw=true", width=300)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b5394ff;
        color: #ffffff;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def main():
    st.title("Stripe Metrics Dashboard Generator")
    api_key = st.text_input("Enter your Stripe API key:", type="password")

    if api_key:
        stripe.api_key = api_key
        try:
            monthly_data, weekly_data = generate_dashboard_metrics()
            latest_month_data = monthly_data.iloc[-1]

            # Display metrics for the latest month
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

            # Plotting the data for the past 12 months
            st.subheader("Monthly Trends Over the Past 12 Months")
            metrics_to_plot = ['GMV', 'Revenue', 'Revenue/GMV Ratio', 'Authorization Rate', 'Dispute Rate', 'Fraud Rate']
            for metric in metrics_to_plot:
                chart_data = monthly_data[['Date', metric]].tail(12)
                fig = px.line(chart_data, x='Date', y=metric, title=metric, markers=True, template='plotly_white')
                fig.update_layout(height=300)  # Adjust the height as necessary
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to generate dashboard: {str(e)}")
    else:
        st.warning("Please enter a valid Stripe API key to generate the dashboard.")

def generate_dashboard_metrics():
    # Define the time period for the data (past 12 months)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=365)

    # Initialize data storage
    weekly_data_list = []
    monthly_data_list = []

    for week_start in pd.date_range(start=start_date, end=today, freq='W-SUN'):
        week_end = week_start + datetime.timedelta(days=6)
        month_end = week_start + datetime.timedelta(days=30)
        week_start_unix = int(time.mktime(week_start.timetuple()))
        week_end_unix = int(time.mktime(week_end.timetuple()))
        month_end_unix = int(time.mktime(month_end.timetuple()))

        payment_intents = stripe.PaymentIntent.list(created={'gte': week_start_unix, 'lte': week_end_unix})
        disputes = stripe.Dispute.list(created={'gte': week_start_unix, 'lte': week_end_unix})

        # Calculate metrics
        approved_payments = sum(1 for pi in payment_intents.data if pi['status'] == 'succeeded')
        total_payments = len(payment_intents.data)
        authorization_rate = (approved_payments / total_payments) * 100 if total_payments > 0 else 0
        disputed_payments = sum(1 for d in disputes.data if d['id'] is not None)
        dispute_rate = (disputed_payments / total_payments) * 100 if total_payments > 0 else 0
        fraudulent_disputes = sum(1 for d in disputes.data if d['reason'] == 'fraudulent')
        fraud_rate = (fraudulent_disputes / total_payments) * 100 if total_payments > 0 else 0
        gmv = sum(pi['amount_received'] for pi in payment_intents.data)
        refunded_amount = sum(ref['amount'] for ref in disputes.data if ref['status'] in ('succeeded', 'pending'))
        chargeback_amount = sum(dis['amount'] for dis in disputes.data if dis['status'] in ('lost', 'warning_closed'))
        revenue = gmv - refunded_amount - chargeback_amount

        # Store data
        weekly_data_list.append({
            'Date': week_end.strftime('%Y-%m-%d'),
            'GMV': gmv,
            'Revenue': revenue,
            'Revenue/GMV Ratio': (revenue / gmv * 100) if gmv > 0 else 0,
            'Authorization Rate': authorization_rate,
            'Dispute Rate': dispute_rate,
            'Fraud Rate': fraud_rate
        })

        # Store monthly data
        if week_end.day >= 28:
            monthly_data_list.append({
                'Date': month_end.strftime('%Y-%m-%d'),
                'GMV': gmv,
                'Revenue': revenue,
                'Revenue/GMV Ratio': (revenue / gmv * 100) if gmv > 0 else 0,
                'Authorization Rate': authorization_rate,
                'Dispute Rate': dispute_rate,
                'Fraud Rate': fraud_rate
            })

    # Convert to DataFrame
    weekly_data = pd.DataFrame(weekly_data_list)
    monthly_data = pd.DataFrame(monthly_data_list)

    return monthly_data, weekly_data

if __name__ == "__main__":
    main()
