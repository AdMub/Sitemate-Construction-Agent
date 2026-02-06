import requests

# Use Paystack Test Keys (Free to get from paystack.com)
PAYSTACK_SECRET = "sk_test_xxxxxxxxxxxxxxxxxxxxxxxx" 

def initialize_payment(email, amount_naira, reference):
    """Generates a Paystack Checkout Link."""
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": int(amount_naira * 100), # Paystack takes amount in Kobo
        "reference": reference,
        "callback_url": "http://localhost:8501" # Redirect back to app
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['data']['authorization_url']
    except:
        pass
    
    # Fallback if no API key is set
    return "https://paystack.com/pay/test-checkout"