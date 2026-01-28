### (This now handles both WhatsApp and Email generation)

import urllib.parse

def generate_order_message(location, boq_dataframe, supplier_name):
    """Creates the text message for orders."""
    grand_total = boq_dataframe['Total Cost'].sum()
    
    message = f"Hello {supplier_name},\n\n"
    message += f"I would like to place an order for a project in *{location}*.\n\n"
    message += "*REQUESTED MATERIALS:*\n"
    
    for _, row in boq_dataframe.iterrows():
        qty_str = f"{row['Qty']:.0f}"
        message += f"- {row['Item']}: {qty_str} units\n"
        
    message += f"\n*Target Budget:* ₦{grand_total:,.0f}\n"
    message += "Please send your official invoice and bank details.\n\nRegards,\nSiteMate User"
    return message

def get_whatsapp_link(phone_number, message):
    """Generates WhatsApp Link."""
    if not phone_number: return None
    
    # Sanitize phone number (Remove + if present)
    clean_number = str(phone_number).replace("+", "").strip()
    
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_number}?text={encoded_msg}"

def get_email_link(email_address, location, message):
    """Generates Mailto Link."""
    if not email_address: return None
    
    subject = f"Order Request - {location} Project"
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(message)
    return f"mailto:{email_address}?subject={encoded_subject}&body={encoded_body}"