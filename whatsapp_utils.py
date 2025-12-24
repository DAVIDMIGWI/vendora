"""Utility functions for sending WhatsApp messages"""
import os
import requests
from flask import current_app
from decimal import Decimal

def send_whatsapp_message(phone_number, message):
    """
    Send a WhatsApp message using the configured API.
    
    Args:
        phone_number: Phone number in international format (e.g., +254712345678)
        message: Message text to send
    
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    # #region agent log
    import json
    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({
            'location': 'whatsapp_utils.py:send_whatsapp_message:entry',
            'message': 'Function called',
            'data': {'phone_number': phone_number, 'message_length': len(message) if message else 0},
            'timestamp': __import__('time').time() * 1000
        }) + '\n')
    # #endregion
    
    # Get WhatsApp API configuration
    whatsapp_api_url = current_app.config.get('WHATSAPP_API_URL')
    whatsapp_api_key = current_app.config.get('WHATSAPP_API_KEY')
    whatsapp_phone_id = current_app.config.get('WHATSAPP_PHONE_ID')
    
    # #region agent log
    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({
            'location': 'whatsapp_utils.py:send_whatsapp_message:config_check',
            'message': 'API configuration check',
            'data': {
                'has_api_url': bool(whatsapp_api_url),
                'has_api_key': bool(whatsapp_api_key),
                'has_phone_id': bool(whatsapp_phone_id),
                'api_url': whatsapp_api_url or 'NOT_SET'
            },
            'timestamp': __import__('time').time() * 1000
        }) + '\n')
    # #endregion
    
    # If no configuration, log and return False (don't fail the order)
    if not whatsapp_api_url or not whatsapp_api_key:
        error_msg = 'WhatsApp API not configured. Set WHATSAPP_API_URL and WHATSAPP_API_KEY environment variables.'
        current_app.logger.warning(error_msg)
        # #region agent log
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'whatsapp_utils.py:send_whatsapp_message:no_config',
                'message': 'WhatsApp API not configured - returning False',
                'data': {
                    'error': error_msg,
                    'api_url_set': bool(whatsapp_api_url),
                    'api_key_set': bool(whatsapp_api_key)
                },
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        print(f"⚠️  {error_msg}")  # Also print to console for visibility
        return False
    
    try:
        # Format phone number (ensure it starts with +)
        if not phone_number.startswith('+'):
            # Assume Kenyan number if no country code
            if phone_number.startswith('0'):
                phone_number = '+254' + phone_number[1:]
            else:
                phone_number = '+254' + phone_number
        
        # For WhatsApp Cloud API (Meta)
        if 'graph.facebook.com' in whatsapp_api_url or 'whatsapp' in whatsapp_api_url.lower() or 'facebook.com' in whatsapp_api_url:
            headers = {
                'Authorization': f'Bearer {whatsapp_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'text',
                'text': {
                    'body': message
                }
            }
            
            # Build URL correctly for Meta WhatsApp API
            # Format: https://graph.facebook.com/v18.0/{phone-number-id}/messages
            if whatsapp_phone_id:
                # If URL already contains version, use it as-is, otherwise add v18.0
                if '/v' in whatsapp_api_url:
                    url = f"{whatsapp_api_url}/{whatsapp_phone_id}/messages"
                else:
                    url = f"{whatsapp_api_url}/v18.0/{whatsapp_phone_id}/messages"
            else:
                # Fallback if no phone_id (shouldn't happen but handle gracefully)
                if '/v' in whatsapp_api_url:
                    url = f"{whatsapp_api_url}/messages"
                else:
                    url = f"{whatsapp_api_url}/v18.0/messages"
            
            # #region agent log
            import json
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'whatsapp_utils.py:send_whatsapp_message:before_api_call',
                    'message': 'About to call WhatsApp API',
                    'data': {'url': url, 'phone_number': phone_number, 'has_phone_id': bool(whatsapp_phone_id)},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'whatsapp_utils.py:send_whatsapp_message:after_api_call',
                    'message': 'WhatsApp API response',
                    'data': {
                        'status_code': response.status_code,
                        'response_text': response.text[:500] if response.text else None,
                        'success': response.status_code in [200, 201]
                    },
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            if response.status_code in [200, 201]:
                current_app.logger.info(f'WhatsApp message sent to {phone_number}')
                return True
            else:
                current_app.logger.error(f'WhatsApp API error: {response.status_code} - {response.text}')
                return False
        
        # For Twilio WhatsApp API
        elif 'twilio.com' in whatsapp_api_url:
            from twilio.rest import Client
            
            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = whatsapp_api_key  # Use API key as auth token for Twilio
            
            if not account_sid or not auth_token:
                current_app.logger.error('Twilio credentials not configured')
                return False
            
            client = Client(account_sid, auth_token)
            
            # Twilio WhatsApp number (from config or default)
            from_number = current_app.config.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
            
            message_obj = client.messages.create(
                body=message,
                from_=from_number,
                to=f'whatsapp:{phone_number}'
            )
            
            current_app.logger.info(f'WhatsApp message sent via Twilio: {message_obj.sid}')
            return True
        
        # Generic HTTP POST (for custom WhatsApp gateways)
        else:
            headers = {
                'Authorization': f'Bearer {whatsapp_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'to': phone_number,
                'message': message
            }
            
            response = requests.post(whatsapp_api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                current_app.logger.info(f'WhatsApp message sent to {phone_number}')
                return True
            else:
                current_app.logger.error(f'WhatsApp API error: {response.status_code} - {response.text}')
                return False
    
    except Exception as e:
        current_app.logger.error(f'Error sending WhatsApp message: {str(e)}')
        return False


def format_order_message(order):
    """
    Format order details into WhatsApp message template.
    
    Args:
        order: Order object with buyer, vendor, items, etc.
    
    Returns:
        str: Formatted message string
    """
    # Customer name
    customer_name = order.buyer.name
    
    # Delivery location
    delivery_location = order.delivery_address
    
    # Delivery instructions
    delivery_instructions = order.delivery_instructions or 'None'
    
    # Build items lines - format: * {name} x{qty} @ Ksh {unit_price}
    items_lines = []
    for item in order.items:
        if not item.is_removed:
            item_name = item.product_name_snapshot
            qty = item.quantity
            unit_price = float(item.unit_price_snapshot)
            
            # Format exactly as specified: * {name} x{qty} @ Ksh {unit_price}
            items_lines.append(f"* {item_name} x{qty} @ Ksh {int(unit_price)}")
    
    items_text = "\n".join(items_lines)
    
    # Total amount
    total_amount = int(float(order.total))
    
    # Build message (exactly as specified in requirements)
    # Note: WhatsApp uses *text* for bold, but keeping ** as user specified
    message = f"""**New Order**
Customer: {customer_name}
Delivery: {delivery_location}
Instructions: {delivery_instructions}

Items:
{items_text}

Total: Ksh {total_amount}"""
    
    return message


def send_order_notification(order):
    """
    Send WhatsApp notification to vendor when a new order is placed.
    
    Args:
        order: Order object
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    # #region agent log
    import json
    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({
            'location': 'whatsapp_utils.py:send_order_notification:entry',
            'message': 'Function called',
            'data': {'order_id': order.id if order else None},
            'timestamp': __import__('time').time() * 1000
        }) + '\n')
    # #endregion
    
    # Get vendor phone number
    vendor = order.vendor
    # #region agent log
    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({
            'location': 'whatsapp_utils.py:send_order_notification:vendor_check',
            'message': 'Vendor check',
            'data': {
                'has_vendor': bool(vendor),
                'vendor_id': vendor.id if vendor else None,
                'vendor_phone': vendor.phone if vendor else None,
                'has_phone': bool(vendor.phone if vendor else None)
            },
            'timestamp': __import__('time').time() * 1000
        }) + '\n')
    # #endregion
    
    if not vendor or not vendor.phone:
        current_app.logger.warning(f'Vendor {vendor.id if vendor else "unknown"} has no phone number. WhatsApp not sent.')
        # #region agent log
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'whatsapp_utils.py:send_order_notification:no_phone',
                'message': 'Vendor has no phone number - returning False',
                'data': {},
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        return False
    
    # Format and send message
    message = format_order_message(order)
    # #region agent log
    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({
            'location': 'whatsapp_utils.py:send_order_notification:before_send',
            'message': 'About to send WhatsApp message',
            'data': {'phone': vendor.phone, 'message_preview': message[:100] if message else None},
            'timestamp': __import__('time').time() * 1000
        }) + '\n')
    # #endregion
    
    result = send_whatsapp_message(vendor.phone, message)
    
    # #region agent log
    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({
            'location': 'whatsapp_utils.py:send_order_notification:after_send',
            'message': 'WhatsApp send result',
            'data': {'result': result},
            'timestamp': __import__('time').time() * 1000
        }) + '\n')
    # #endregion
    
    return result

