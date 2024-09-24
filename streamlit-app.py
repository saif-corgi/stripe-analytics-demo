import streamlit as st
import datetime
import stripe
import time
import pandas as pd
import plotly.express as px
# To center the logo, you can use Streamlit's columns to center the image.
# First, ensure your image is hosted and publicly accessible, as previously described.

# Setting up theme customization via Python
st.set_page_config(
    page_title="Payments & Fraud Overview",
    menu_items={
        'Get Help': 'https://www.corgilabs.ai',
        'About': "# Get powerful insights on your payments, using only your Stripe API key!"
    }
)

st.markdown("""
<style>
button {
    border: none;
    outline: none;
    background-color: transparent;  /* Hide button appearance */
}

button:hover {
    border: none;  /* Remove border on hover */
    outline: none;
}

button:focus {
    outline: none;  /* Remove focus when clicked */
}

div.stButton > button {
    height: 100%;  /* Extend the button area to cover the entire image */
    width: 100%;
}

/* Adjust image sizing and alignment */
img {
    display: block;
    margin: auto;
    max-width: 100%;  /* Ensures the image is contained within the button */
    height: auto;
}
</style>
""", unsafe_allow_html=True)

# Example using a direct link from Google Drive:
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("https://github.com/saif-corgi/stripe-analytics-demo/blob/main/CorgiAI%20logo%20(white%20background)%201200.png?raw=true", width=300)

# Streamlit app to input Stripe API key and generate dashboard
def main():
    st.markdown("<h1 style='text-align: center; color: black; margin-bottom: 20px;'>Payments & Fraud Overview</h1>", unsafe_allow_html=True)
    # st.markdown("<h2 style='text-align: center; color: black; margin-bottom: 20px;'>Select a payment provider</h2>", unsafe_allow_html=True)
    
    api_provider = 'Stripe'
    api_key = st.text_input("Enter your Stripe API key:", type="password")
    account_id = st.text_input("Enter your Stripe account ID:", type="password")

    # col1, col2, col3 = st.columns(3)
    
    # image_url_stripe = "https://github.com/saif-corgi/stripe-analytics-demo/blob/main/stripe.png?raw=true"
    # image_url_adyen = "https://github.com/saif-corgi/stripe-analytics-demo/blob/main/adyen.png?raw=true"
    # image_url_shopify = "https://github.com/saif-corgi/stripe-analytics-demo/blob/main/shopify.png?raw=true"
    
    # # Define a key for the button-like image in the session state
    # if 'selected_provider' not in st.session_state:
    #     st.session_state.selected_provider = None
    
    # def select_provider(provider):
    #     st.session_state.selected_provider = provider
    
    # # Streamlit columns for layout
    # col1, col2, col3 = st.columns(3)
    
    # # Using buttons to trigger provider selection
    # with col1:
    #     if st.button("", key="stripe", help="Click to select Stripe as your provider"):
    #         select_provider("Stripe")
    #     st.image(image_url_stripe, width=200)
    
    # with col2:
    #     if st.button("", key="adyen", help="Click to select Adyen as your provider"):
    #         select_provider("Adyen")
    #     st.image(image_url_adyen, width=200)
    
    # with col3:
    #     if st.button("", key="shopify", help="Click to select Shopify as your provider"):
    #         select_provider("Shopify")
    #     st.image(image_url_shopify, width=200)
    
    # # Check which provider was selected and respond accordingly
    # if st.session_state.selected_provider == 'Stripe':
    #     api_key = st.text_input("Enter your Stripe API key:", type="password")
    #     if api_key:
    #         st.session_state.api_provider = 'Stripe'
    #         api_provider = 'Stripe'
    # elif st.session_state.selected_provider == 'Adyen':
    #     st.session_state.api_provider = 'Adyen'
    #     if st.button("Schedule a call with us for Adyen"):
    #         st.markdown("[Schedule a call](https://calendly.com/saif_corgiai/saif-corgi-labs)", unsafe_allow_html=True)
    # elif st.session_state.selected_provider == 'Shopify':
    #     st.session_state.api_provider = 'Shopify'
    #     if st.button("Schedule a call with us for Shopify"):
    #         st.markdown("[Schedule a call](https://calendly.com/saif_corgiai/saif-corgi-labs)", unsafe_allow_html=True)      
            
    if api_key:
        stripe.api_key = api_key
        try:
            monthly_data, weekly_data = generate_dashboard_metrics(account_id)
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
            
            # Plotting the data for the past 12 months
            st.subheader("Monthly Trends Over the Past 12 Months")
            metrics_to_plot = ['GMV', 'Revenue', 'Revenue/GMV Ratio', 'Authorization Rate', 'Dispute Rate', 'Fraud Rate']
            col1, col2 = st.columns(2)
            for i, metric in enumerate(metrics_to_plot):
                chart_data = monthly_data.set_index('Date')[metric].tail(12)  # Select only the last 12 months
                with col1 if i % 2 == 0 else col2:
                    st.markdown(f"**{metric}**", unsafe_allow_html=True)
                    if metric in ['GMV', 'Revenue']:
                        st.bar_chart(chart_data, height=300, use_container_width=True)
                    elif metric == 'Revenue/GMV Ratio':
                        chart_data = (monthly_data['Revenue'] / monthly_data['GMV'] * 100).tail(12)
                        chart_data.index = pd.to_datetime(chart_data.index).strftime('%B %Y')
                        st.line_chart(chart_data, height=300, use_container_width=True)
                    else:
                        chart_data.index = pd.to_datetime(chart_data.index).strftime('%B %Y')
                        st.line_chart(chart_data, height=300, use_container_width=True)
                                      # disable_xscroll=True, line_width=3)

        except Exception as e:
            st.error(f"Failed to generate dashboard: {str(e)}")
    else:
        st.warning("Please enter a valid API key to generate the dashboard.")
         
    
def generate_dashboard_metrics(account_id):
    # Define the time period for the data (past 12 months)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=365)

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
            created={'gte': week_start_unix, 'lte': week_end_unix},
            stripe_account=account_id
        )
        disputes = stripe.Dispute.list(
            created={'gte': week_start_unix, 'lte': week_end_unix},
            stripe_account=account_id
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
