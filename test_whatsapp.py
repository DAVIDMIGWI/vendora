"""Test script for Africa's Talking notifications with vendor Mary"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Vendor, Order, User
from notification_service import NotificationService

app = create_app('development')

with app.app_context():
    # Find vendor by phone number 0726143237 (Mary's vendor)
    vendor = Vendor.query.filter_by(phone='0726143237').first()
    
    # If not found, try finding by shop name containing 'mary' or 'fresh'
    if not vendor:
        vendors = Vendor.query.filter(
            (Vendor.shop_name.ilike('%mary%')) | 
            (Vendor.shop_name.ilike('%fresh%'))
        ).all()
        vendor = vendors[0] if vendors else None
    
    print("=" * 60)
    print("Testing WhatsApp with Vendor (Phone: 0726143237)")
    print("=" * 60)
    
    if not vendor:
        print("❌ No vendor found with phone 0726143237")
        print("\nAll vendors:")
        all_vendors = Vendor.query.all()
        for v in all_vendors:
            print(f"  - {v.shop_name} (ID: {v.id}, Phone: {v.phone})")
    else:
        print(f"✅ Found vendor: {vendor.shop_name}")
        print(f"   ID: {vendor.id}")
        print(f"   Phone: {vendor.phone}")
        print(f"   Status: {vendor.status}")
        
        # Update phone numbers if needed
        phone_number_e164 = '+254726143237'  # E.164 format
        
        # Update phone_number field (E.164)
        if not vendor.phone_number or vendor.phone_number != phone_number_e164:
            print(f"\n📱 Updating phone numbers...")
            vendor.phone_number = phone_number_e164
            vendor.whatsapp_number = phone_number_e164  # Use same number for WhatsApp
            vendor.whatsapp_opt_in = True  # Enable WhatsApp opt-in for testing
            if not vendor.phone:
                vendor.phone = '0726143237'  # Keep legacy field
            db.session.commit()
            print(f"   ✅ Phone number updated to {phone_number_e164}")
            print(f"   ✅ WhatsApp number set to {phone_number_e164}")
            print(f"   ✅ WhatsApp opt-in enabled")
        
        # Check for recent order
        recent_order = Order.query.filter_by(vendor_id=vendor.id).order_by(Order.created_at.desc()).first()
        
        if recent_order:
            print(f"\n✅ Found recent order: Order #{recent_order.id}")
            print(f"   Buyer: {recent_order.buyer.name}")
            print(f"   Total: KSh {recent_order.total}")
            
            # Format message
            print("\n" + "=" * 60)
            print("Formatted Notification Message:")
            print("=" * 60)
            notification_service = NotificationService()
            message = notification_service.format_order_message(recent_order)
            print(message)
            print("=" * 60)
            
            # Check Africa's Talking API configuration
            print("\n📋 Africa's Talking API Configuration:")
            at_username = app.config.get('AT_USERNAME')
            at_api_key = app.config.get('AT_API_KEY')
            at_env = app.config.get('AT_ENV', 'sandbox')
            at_template = app.config.get('AT_WHATSAPP_TEMPLATE_NAME', 'order_notification')
            
            print(f"   Username: {at_username or 'NOT SET'}")
            print(f"   API Key: {'SET' if at_api_key else 'NOT SET'}")
            print(f"   Environment: {at_env}")
            print(f"   WhatsApp Template: {at_template}")
            
            if not at_username or not at_api_key:
                print("\n❌ Africa's Talking API not configured!")
                print("   Set environment variables:")
                print("   export AT_USERNAME='Vendora'")
                print("   export AT_API_KEY='your_at_api_key'")
                print("   export AT_ENV='sandbox'")
                print("   export AT_WHATSAPP_TEMPLATE_NAME='order_notification'")
            else:
                print("\n🚀 Attempting to send notification...")
                print(f"   Vendor WhatsApp opt-in: {vendor.whatsapp_opt_in}")
                print(f"   Vendor WhatsApp number: {vendor.whatsapp_number}")
                print(f"   Vendor phone number: {vendor.phone_number}")
                
                result = notification_service.notify_vendor(recent_order.id)
                
                # Refresh order to get updated status
                db.session.refresh(recent_order)
                
                if result:
                    print("✅ Notification sent successfully!")
                    if recent_order.whatsapp_status:
                        print(f"   WhatsApp Status: {recent_order.whatsapp_status}")
                        print(f"   WhatsApp Message ID: {recent_order.whatsapp_message_id}")
                    if recent_order.sms_status:
                        print(f"   SMS Status: {recent_order.sms_status}")
                        print(f"   SMS Message ID: {recent_order.sms_message_id}")
                else:
                    print("❌ Failed to send notification. Check debug.log for details.")
                    if recent_order.whatsapp_status:
                        print(f"   WhatsApp Status: {recent_order.whatsapp_status}")
                    if recent_order.sms_status:
                        print(f"   SMS Status: {recent_order.sms_status}")
        else:
            print("\n⚠️  No orders found for this vendor.")
            print("   Please place an order first, then run this test again.")
    
    print("\n" + "=" * 60)
    print("Check debug.log for detailed logs")
    print("=" * 60)

