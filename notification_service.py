"""Notification service using Africa's Talking for SMS and WhatsApp"""
import os
import requests
import africastalking
from flask import current_app
from models import db, Order

class NotificationService:
    """Service for sending SMS and WhatsApp notifications via Africa's Talking"""
    
    def __init__(self):
        self.env = current_app.config.get('AT_ENV', 'sandbox')
        # For sandbox, username is always 'sandbox'
        # For production/live, use the configured username
        if self.env == 'sandbox':
            self.username = 'sandbox'
        else:
            self.username = current_app.config.get('AT_USERNAME')
        
        self.api_key = current_app.config.get('AT_API_KEY')
        # Only use sender_id if explicitly configured (must be approved/registered)
        self.sms_from = current_app.config.get('AT_SMS_FROM')  # None if not set
        self.whatsapp_template = current_app.config.get('AT_WHATSAPP_TEMPLATE_NAME', 'order_notification')
        self.whatsapp_url = current_app.config.get('AT_WHATSAPP_URL', '')
        
        # #region agent log
        import json
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'notification_service.py:__init__',
                'message': 'NotificationService initialized',
                'data': {
                    'username': self.username or 'NOT SET',
                    'api_key_set': bool(self.api_key),
                    'env': self.env,
                    'sms_from': self.sms_from or 'NOT SET (will use default)'
                },
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        
        # Initialize Africa's Talking SDK
        if self.username and self.api_key:
            try:
                africastalking.initialize(self.username, self.api_key)
                self.sms = africastalking.SMS
                # #region agent log
                with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        'location': 'notification_service.py:__init__:sdk_init',
                        'message': 'Africa\'s Talking SDK initialized',
                        'data': {},
                        'timestamp': __import__('time').time() * 1000
                    }) + '\n')
                # #endregion
            except Exception as e:
                current_app.logger.error(f'Failed to initialize Africa\'s Talking SDK: {str(e)}')
                self.sms = None
        else:
            self.sms = None
    
    def _format_phone(self, phone_number):
        """Format phone number to E.164 format"""
        if not phone_number:
            return None
        if not phone_number.startswith('+'):
            if phone_number.startswith('0'):
                return '+254' + phone_number[1:]
            else:
                return '+254' + phone_number
        return phone_number
    
    def send_sms(self, to, message):
        """
        Send SMS using Africa's Talking SDK
        
        Args:
            to: Phone number in E.164 format (e.g., +254712345678)
            message: Message text to send
        
        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        # #region agent log
        import json
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'notification_service.py:send_sms:entry',
                'message': 'Sending SMS',
                'data': {'to': to, 'message_length': len(message) if message else 0},
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        
        if not self.sms:
            error = 'Africa\'s Talking SDK not initialized. Check credentials.'
            current_app.logger.error(error)
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_sms:no_sdk',
                    'message': error,
                    'data': {},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            return False, None, error
        
        # Format phone number
        to = self._format_phone(to)
        if not to:
            error = 'Invalid phone number'
            return False, None, error
        
        try:
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_sms:before_sdk_call',
                    'message': 'About to call AT SMS SDK',
                    'data': {'to': to, 'sms_from': self.sms_from or 'None (using default)'},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            # Use Africa's Talking SDK
            # Only pass sender_id if explicitly configured (must be approved/registered)
            if self.sms_from:
                response = self.sms.send(
                    message=message,
                    recipients=[to],
                    sender_id=self.sms_from
                )
            else:
                # Don't pass sender_id - let AT use default
                response = self.sms.send(
                    message=message,
                    recipients=[to]
                )
            
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_sms:after_sdk_call',
                    'message': 'AT SMS SDK response',
                    'data': {'response_type': type(response).__name__, 'response': str(response)[:500] if response else None},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            # Parse response - SDK returns dict-like object
            if response and isinstance(response, dict):
                recipients = response.get("SMSMessageData", {}).get("Recipients", [])
                if recipients:
                    recipient = recipients[0]
                    status = recipient.get('status')
                    message_id = recipient.get('messageId')
                    status_code = recipient.get('statusCode', 'N/A')
                    cost = recipient.get('cost', 'N/A')
                    
                    # #region agent log
                    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            'location': 'notification_service.py:send_sms:parsed_response',
                            'message': 'Parsed SMS response',
                            'data': {
                                'status': status,
                                'status_code': status_code,
                                'message_id': message_id,
                                'cost': cost,
                                'number': recipient.get('number')
                            },
                            'timestamp': __import__('time').time() * 1000
                        }) + '\n')
                    # #endregion
                    
                    if status == 'Success':
                        # IMPORTANT: In sandbox, messages are accepted but may NOT be delivered to real phones
                        # Status "Success" means accepted by API, not necessarily delivered to recipient
                        # Sandbox is for API testing only, not actual message delivery
                        current_app.logger.info(f'SMS accepted by API to {to}, messageId: {message_id}, cost: {cost}')
                        if self.env == 'sandbox':
                            current_app.logger.warning(
                                f'SANDBOX LIMITATION: Message {message_id} was accepted by API but may NOT be delivered to {to}. '
                                'Sandbox environment does not deliver to real phone numbers. '
                                'To receive actual SMS, switch to LIVE environment with production credentials.'
                            )
                        return True, message_id, None
                    else:
                        error = f"{status_code} - {recipient.get('statusDescription', 'Unknown error')}"
                        return False, None, error
                else:
                    return False, None, 'No recipients in response'
            else:
                # Unexpected response format
                return False, None, f'Unexpected response format: {type(response)}'
        
        except Exception as e:
            error = f'Error sending SMS: {str(e)}'
            current_app.logger.error(error, exc_info=True)
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_sms:exception',
                    'message': 'Exception during SMS send',
                    'data': {'error': str(e)},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            return False, None, error
    
    def send_whatsapp_template(self, to, variables):
        """
        Send WhatsApp template message using Africa's Talking API
        
        Args:
            to: Phone number in E.164 format
            variables: Dict of template variables
        
        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        # #region agent log
        import json
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'notification_service.py:send_whatsapp_template:entry',
                'message': 'Sending WhatsApp template',
                'data': {'to': to, 'template': self.whatsapp_template, 'variables': list(variables.keys()) if variables else []},
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        
        if not self.whatsapp_url:
            error = 'WhatsApp URL not configured'
            current_app.logger.error(error)
            return False, None, error
        
        if not self.username or not self.api_key:
            error = 'Africa\'s Talking credentials not configured'
            return False, None, error
        
        # Format phone number
        to = self._format_phone(to)
        if not to:
            return False, None, 'Invalid phone number'
        
        try:
            payload = {
                "username": self.username,
                "to": to,
                "template": self.whatsapp_template,
                "variables": variables
            }
            
            headers = {
                "apiKey": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_whatsapp_template:before_api_call',
                    'message': 'About to call AT WhatsApp API',
                    'data': {'url': self.whatsapp_url, 'to': to, 'template': self.whatsapp_template},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            response = requests.post(
                self.whatsapp_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_whatsapp_template:after_api_call',
                    'message': 'AT WhatsApp API response',
                    'data': {
                        'status_code': response.status_code,
                        'response_text': response.text[:500] if response.text else None
                    },
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    message_id = result.get('messageId') or result.get('id')
                    current_app.logger.info(f'WhatsApp template sent to {to}, messageId: {message_id}')
                    return True, message_id, None
                except Exception as e:
                    return False, None, f'Failed to parse response: {str(e)}'
            else:
                error = f'AT WhatsApp API error: {response.status_code} - {response.text}'
                current_app.logger.error(error)
                return False, None, error
        
        except Exception as e:
            error = f'Error sending WhatsApp: {str(e)}'
            current_app.logger.error(error, exc_info=True)
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:send_whatsapp_template:exception',
                    'message': 'Exception during WhatsApp send',
                    'data': {'error': str(e)},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            return False, None, error
    
    def format_order_message(self, order):
        """
        Format order details into notification message
        
        Args:
            order: Order object
        
        Returns:
            str: Formatted message
        """
        customer_name = order.buyer.name
        delivery_location = order.delivery_address
        delivery_instructions = order.delivery_instructions or 'None'
        
        # Build items lines
        items_lines = []
        for item in order.items:
            if not item.is_removed:
                item_name = item.product_name_snapshot
                qty = item.quantity
                unit_price = int(float(item.unit_price_snapshot))
                items_lines.append(f"- {item_name} x{qty} @ Ksh {unit_price}")
        
        items_text = "\n".join(items_lines)
        total_amount = int(float(order.total))
        
        # Format message (without **New Order** header as specified)
        message = f"""Customer: {customer_name}
Delivery: {delivery_location}
Instructions: {delivery_instructions}

Items:
{items_text}

Total: Ksh {total_amount}"""
        
        return message
    
    def notify_vendor(self, order_id):
        """
        Notify vendor about a new order via WhatsApp (with SMS fallback)
        
        Args:
            order_id: Order ID
        
        Returns:
            bool: True if notification sent (via WhatsApp or SMS), False otherwise
        """
        # #region agent log
        import json
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'notification_service.py:notify_vendor:entry',
                'message': 'Notifying vendor',
                'data': {'order_id': order_id},
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        
        order = Order.query.get(order_id)
        if not order:
            current_app.logger.error(f'Order {order_id} not found')
            return False
        
        vendor = order.vendor
        if not vendor:
            current_app.logger.error(f'Vendor not found for order {order_id}')
            return False
        
        # Format message
        message = self.format_order_message(order)
        
        # Prepare template variables for WhatsApp
        customer_name = order.buyer.name
        delivery_location = order.delivery_address
        delivery_instructions = order.delivery_instructions or 'None'
        
        # Build items text for template variable
        items_lines = []
        for item in order.items:
            if not item.is_removed:
                item_name = item.product_name_snapshot
                qty = item.quantity
                unit_price = int(float(item.unit_price_snapshot))
                items_lines.append(f"{item_name} x{qty} @ Ksh {unit_price}")
        items_text = "\n".join(items_lines)
        total_amount = int(float(order.total))
        
        whatsapp_variables = {
            "customer_name": customer_name,
            "delivery_location": delivery_location,
            "delivery_instructions": delivery_instructions,
            "items_lines": items_text,
            "total_amount": str(total_amount)
        }
        
        # Try WhatsApp first (if vendor has WhatsApp opt-in)
        whatsapp_sent = False
        
        # #region agent log
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'notification_service.py:notify_vendor:check_whatsapp',
                'message': 'Checking WhatsApp availability',
                'data': {
                    'vendor_id': vendor.id,
                    'whatsapp_opt_in': getattr(vendor, 'whatsapp_opt_in', False),
                    'whatsapp_number': getattr(vendor, 'whatsapp_number', None),
                    'phone_number': getattr(vendor, 'phone_number', None) or vendor.phone
                },
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        
        if getattr(vendor, 'whatsapp_opt_in', False) and getattr(vendor, 'whatsapp_number', None):
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:notify_vendor:try_whatsapp',
                    'message': 'Attempting WhatsApp notification',
                    'data': {'whatsapp_number': vendor.whatsapp_number},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            success, message_id, error = self.send_whatsapp_template(
                vendor.whatsapp_number,
                whatsapp_variables
            )
            
            # Update order with WhatsApp status
            if success:
                order.whatsapp_status = 'sent'
                order.whatsapp_message_id = message_id
                whatsapp_sent = True
            else:
                order.whatsapp_status = 'failed'
                current_app.logger.warning(f'WhatsApp failed for order {order_id}: {error}')
            
            db.session.commit()
        
        # Fallback to SMS if WhatsApp failed or not available
        if not whatsapp_sent:
            # Use phone_number field (E.164) if exists, otherwise use legacy phone field
            phone_number = getattr(vendor, 'phone_number', None) or vendor.phone
            
            # #region agent log
            with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'notification_service.py:notify_vendor:try_sms',
                    'message': 'Attempting SMS fallback',
                    'data': {'phone_number': phone_number, 'whatsapp_sent': whatsapp_sent},
                    'timestamp': __import__('time').time() * 1000
                }) + '\n')
            # #endregion
            
            if phone_number:
                success, message_id, error = self.send_sms(phone_number, message)
                
                # Update order with SMS status
                if success:
                    order.sms_status = 'sent'
                    order.sms_message_id = message_id
                else:
                    order.sms_status = 'failed'
                    current_app.logger.error(f'SMS failed for order {order_id}: {error}')
                
                db.session.commit()
                return success
            else:
                current_app.logger.error(f'No phone number available for vendor {vendor.id}')
                return False
        
        return whatsapp_sent
