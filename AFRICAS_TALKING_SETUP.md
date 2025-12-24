# Africa's Talking Notification Setup

This application uses Africa's Talking API for sending SMS and WhatsApp notifications to vendors when orders are placed.

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root with:

```env
AT_USERNAME=Vendora
AT_API_KEY=your_at_api_key_here
AT_ENV=sandbox
AT_WHATSAPP_TEMPLATE_NAME=order_notification
```

**Important:** Never commit the `.env` file with real API keys to version control.

### 2. Database Migration

Run the migration script to add notification fields:

```bash
python3 migrate_add_notification_fields.py
```

This will add:
- `phone_number`, `whatsapp_number`, `whatsapp_opt_in` to `vendors` table
- `sms_status`, `sms_message_id`, `whatsapp_status`, `whatsapp_message_id` to `orders` table

### 3. WhatsApp Template Setup

**Before using WhatsApp notifications**, you must:

1. Log in to [Africa's Talking Dashboard](https://account.africastalking.com/)
2. Navigate to WhatsApp section
3. Create a template with the name specified in `AT_WHATSAPP_TEMPLATE_NAME` (default: `order_notification`)
4. The template must have **5 variables** in this order:
   - `customer_name`
   - `delivery_location`
   - `delivery_instructions`
   - `items_lines` (multi-line text with items)
   - `total_amount`

Example template body:
```
Customer: {{1}}
Delivery: {{2}}
Instructions: {{3}}

Items:
{{4}}

Total: Ksh {{5}}
```

### 4. Vendor Configuration

For each vendor, set:
- `phone_number`: E.164 format (e.g., +254712345678) for SMS
- `whatsapp_number`: E.164 format for WhatsApp
- `whatsapp_opt_in`: `true` if vendor has opted in for WhatsApp

## How It Works

1. **Order Placement**: When a buyer places an order, the system automatically calls `notify_vendor(order_id)`

2. **Notification Flow**:
   - **First**: Attempts WhatsApp if vendor has `whatsapp_opt_in=true` and `whatsapp_number` set
   - **Fallback**: If WhatsApp fails or not available, sends SMS to `phone_number`

3. **Message Format**:
   ```
   Customer: {customer_name}
   Delivery: {delivery_location}
   Instructions: {delivery_instructions}

   Items:
   - {item_name} x{qty} @ Ksh {unit_price}
   - ...

   Total: Ksh {total_amount}
   ```

4. **Status Tracking**: Each order stores:
   - `sms_status`: 'queued', 'sent', or 'failed'
   - `sms_message_id`: Message ID from Africa's Talking
   - `whatsapp_status`: 'queued', 'sent', or 'failed'
   - `whatsapp_message_id`: Message ID from Africa's Talking

## Testing

### Test with Sandbox

1. Set `AT_ENV=sandbox` in `.env`
2. Use Africa's Talking sandbox credentials
3. Test phone numbers must be registered in sandbox

### Test Script

Run the test script to verify configuration:

```bash
python3 test_whatsapp.py
```

## Production Setup

1. Switch to live environment:
   ```env
   AT_ENV=live
   ```

2. Update API credentials with production keys

3. Ensure all vendors have correct phone numbers in E.164 format

4. Verify WhatsApp templates are approved in production

## Troubleshooting

- **No notifications sent**: Check `.cursor/debug.log` for detailed logs
- **WhatsApp fails**: Verify template name matches exactly in AT dashboard
- **SMS fails**: Check phone number format (must be E.164: +254...)
- **API errors**: Verify `AT_USERNAME` and `AT_API_KEY` are correct

