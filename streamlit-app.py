# This is a steamlit version, try it out
# End Generation Here
import streamlit as st
import datetime
pip install stripe
import stripe

# Streamlit app to input Stripe API key and generate dashboard
def main():
    st.title("Stripe Metrics Dashboard Generator")
    api_key = st.text_input("Enter your Stripe API key:", type="password")

    if api_key:
        stripe.api_key = api_key
        try:
            # Assuming the rest of the code is properly defined to use the given API key
            metrics, evaluation = generate_dashboard_metrics()
            st.write("Metrics:", metrics)
            st.write("Evaluation:", evaluation)
        except Exception as e:
            st.error(f"Failed to generate dashboard: {str(e)}")
    else:
        st.warning("Please enter a valid Stripe API key to generate the dashboard.")

def generate_dashboard_metrics():
    # Placeholder for the function that generates metrics and evaluation
    # This should include all the necessary computations and data fetching
    # For now, we'll return dummy data

    # Define the time period for the data (last month)
    today = datetime.date.today()
    first_day_last_month = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    last_day_last_month = today.replace(day=1) - datetime.timedelta(days=1)

    # Fetch data from Stripe
    payment_intents = stripe.PaymentIntent.list(
        created={'gte': int(first_day_last_month.strftime('%s')), 'lte': int(last_day_last_month.strftime('%s'))}
    )
    disputes = stripe.Dispute.list(
        created={'gte': int(first_day_last_month.strftime('%s')), 'lte': int(last_day_last_month.strftime('%s'))}
    )
    customers = stripe.Customer.list(
        created={'gte': int(first_day_last_month.strftime('%s')), 'lte': int(last_day_last_month.strftime('%s'))}
    )
    payment_methods = stripe.PaymentMethod.list(
        created={'gte': int(first_day_last_month.strftime('%s')), 'lte': int(last_day_last_month.strftime('%s'))}
    )
    cards = stripe.Card.list(
        created={'gte': int(first_day_last_month.strftime('%s')), 'lte': int(last_day_last_month.strftime('%s'))}
    )
    # Calculate Authorization Rate using Python
    approved_payments = sum(1 for pi in payment_intents.data if pi['charges']['data'][0]['outcome']['network_status'] == 'approved_by_network')
    total_payments = len(set(pi.id for pi in payment_intents.data))
    authorization_rate = (approved_payments / total_payments) * 100 if total_payments > 0 else 0
    authorization_rate = f"{authorization_rate:.2f}%"

    # Calculate Dispute Rate using Python
    disputed_payments = sum(1 for d in disputes.data if d['id'] is not None)
    dispute_rate = (disputed_payments / total_payments) * 100 if total_payments > 0 else 0
    dispute_rate = f"{dispute_rate:.2f}%"

    # Calculate Fraud Rate using Python
    fraudulent_disputes = sum(1 for d in disputes.data if d['id'] is not None and d['reason'] == 'fraudulent')
    fraud_rate = (fraudulent_disputes / total_payments) * 100 if total_payments > 0 else 0
    fraud_rate = f"{fraud_rate:.2f}%"
    # Calculate GMV and Revenue using Python
    gmv = sum(pi['amount'] for pi in payment_intents.data)
    
    # Calculate refunded amount from refund data
    refunded_amount = sum(ref['amount'] for ref in disputes.data if ref['status'] in ('succeeded', 'pending'))
    
    # Calculate chargeback amount from dispute data
    chargeback_amount = sum(dis['amount'] for dis in disputes.data if dis['status'] in ('lost', 'warning_closed'))
    
    # Calculate revenue
    revenue = gmv - refunded_amount - chargeback_amount

    metrics = {
        'GMV': gmv,
        'Revenue': revenue,
        'Authorization Rate': authorization_rate,
        'Dispute Rate': dispute_rate,
        'Fraud Rate': fraud_rate
    }

    # Evaluate metrics
    evaluation = {
        'Revenue/GMV ratio': 'Good' if (revenue / gmv * 100) >= 90 else 'Needs Improvement',
        'Authorization Rate': 'Good' if float(authorization_rate.strip('%')) > 92 else 'Needs Improvement',
        'Dispute Rate': 'Good' if float(dispute_rate.strip('%')) < 0.3 else 'Needs Improvement',
        'Fraud Rate': 'Good' if float(fraud_rate.strip('%')) < 0.3 else 'Needs Improvement'
    }
    return metrics, evaluation

if __name__ == "__main__":
    main()
