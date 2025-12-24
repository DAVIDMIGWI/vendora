"""Test script to verify Africa's Talking credentials"""
import africastalking
import os

# IMPORTANT: For sandbox, username is always "sandbox"
# For production/live, use your actual username
ENV = os.getenv('AT_ENV', 'sandbox')  # 'sandbox' or 'live'

if ENV == 'sandbox':
    USERNAME = "sandbox"
else:
    USERNAME = os.getenv('AT_USERNAME', 'Vendora')  # Your production username

# ⚠️ SECURITY: Regenerate this API key after testing - it was exposed!
API_KEY = os.getenv('AT_API_KEY', 'atsk_9c05dd91ea56a9a2be4fd044826c8017b609a780f485a1b8ea582b432ae8d0e505a9ff2d')
TEST_PHONE = '+254726143237'

print('=' * 60)
print('Testing Africa\'s Talking Credentials')
print('=' * 60)
print(f'Environment: {ENV}')
print(f'Username: {USERNAME}')
print(f'API Key: {API_KEY[:30]}...')
print(f'Test Phone: {TEST_PHONE}')
print()
print('⚠️  SECURITY WARNING: This API key was exposed in chat.')
print('   Please regenerate it in Africa\'s Talking dashboard!')
print()

# Initialize SDK
try:
    print('Initializing SDK...')
    africastalking.initialize(USERNAME, API_KEY)
    sms = africastalking.SMS
    print('✅ SDK initialized successfully')
    print()
except Exception as e:
    print(f'❌ Failed to initialize SDK: {e}')
    exit(1)

# Test SMS
try:
    print('Sending test SMS...')
    message = 'Test message from Vendora notification system'
    
    # Don't pass sender_id unless you have an approved Sender ID
    # For testing, let AT use default
    response = sms.send(
        message=message,
        recipients=[TEST_PHONE]
    )
    
    print(f'Response type: {type(response)}')
    print(f'Raw response: {response}')
    print()
    
    # Parse response - SDK returns dict
    if isinstance(response, dict):
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        if recipients:
            recipient = recipients[0]
            status = recipient.get('status')
            message_id = recipient.get('messageId')
            status_code = recipient.get('statusCode', 'N/A')
            cost = recipient.get('cost', 'N/A')
            
            print('📊 SMS Result:')
            print(f'   Status: {status}')
            print(f'   Message ID: {message_id}')
            print(f'   Status Code: {status_code}')
            print(f'   Cost: {cost}')
            
            if status == 'Success':
                print()
                print('✅ SMS SENT SUCCESSFULLY!')
            else:
                print()
                print(f'❌ SMS failed: {status_code}')
                if recipient.get('statusDescription'):
                    print(f'   Description: {recipient.get("statusDescription")}')
        else:
            print('❌ No recipients in response')
            print(f'Full response: {response}')
    else:
        print('Unexpected response format:')
        print(response)
        
except Exception as e:
    print(f'❌ Error sending SMS: {e}')
    print(f'Error type: {type(e).__name__}')
    
    # Provide helpful error messages
    error_str = str(e)
    if 'authentication' in error_str.lower() or 'invalid' in error_str.lower():
        print()
        print('💡 Authentication Error - Check:')
        print('   1. For sandbox, username must be "sandbox"')
        print('   2. API key matches the username in AT dashboard')
        print('   3. Wait 3 minutes after generating new API key')
        print('   4. API key is for correct environment (sandbox vs live)')
    elif 'balance' in error_str.lower() or 'insufficient' in error_str.lower():
        print()
        print('💡 Balance Error - Add SMS credits to your account')
    elif 'sender' in error_str.lower():
        print()
        print('💡 Sender ID Error - Remove sender_id or use approved Sender ID')
    
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('Next Steps:')
print('1. If authentication failed, verify credentials in AT dashboard')
print('2. For sandbox, username must be "sandbox"')
print('3. Regenerate API key if it was exposed')
print('4. Wait 3 minutes after generating new key before testing')
print('=' * 60)
