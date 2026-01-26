"""Utility functions for Vendora"""
import math
from decimal import Decimal
import os
import smtplib
import ssl
from email.message import EmailMessage

def send_email_smtp(to_email: str, subject: str, text_body: str, html_body: str | None = None):
    """
    Send an email using SMTP configured via environment variables.

    Env vars:
      - SMTP_HOST (required)
      - SMTP_PORT (optional, default 587)
      - SMTP_USERNAME (optional)
      - SMTP_PASSWORD (optional)
      - SMTP_USE_TLS (optional, default true)
      - SMTP_FROM (optional, default SMTP_USERNAME)
    """
    host = os.environ.get('SMTP_HOST')
    if not host:
        raise RuntimeError('SMTP_HOST is not configured')

    port = int(os.environ.get('SMTP_PORT', '587'))
    username = os.environ.get('SMTP_USERNAME')
    password = os.environ.get('SMTP_PASSWORD')
    use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    sender = os.environ.get('SMTP_FROM') or username
    if not sender:
        raise RuntimeError('SMTP_FROM or SMTP_USERNAME must be configured')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()

    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls(context=context)
            smtp.ehlo()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    Returns distance in kilometers.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
    
    Returns:
        Distance in kilometers (float)
    """
    if not all([lat1, lon1, lat2, lon2]):
        return None
    
    # Convert Decimal to float if needed
    lat1 = float(lat1) if isinstance(lat1, Decimal) else lat1
    lon1 = float(lon1) if isinstance(lon1, Decimal) else lon1
    lat2 = float(lat2) if isinstance(lat2, Decimal) else lat2
    lon2 = float(lon2) if isinstance(lon2, Decimal) else lon2
    
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return round(distance, 2)

def get_vendors_within_radius(vendors, user_lat, user_lon, max_radius_km=1.0):
    """
    Filter vendors within a specified radius from user's location.
    
    Args:
        vendors: List of Vendor objects
        user_lat: User's latitude
        user_lon: User's longitude
        max_radius_km: Maximum radius in kilometers (default 1.0, max 1.0)
    
    Returns:
        List of tuples: (vendor, distance_km) sorted by distance
    """
    # Enforce maximum of 1km (allow 0.2, 0.5, or 1.0)
    if max_radius_km not in [0.2, 0.5, 1.0]:
        max_radius_km = min(max_radius_km, 1.0)
    
    if not user_lat or not user_lon:
        # If user has no location, return all vendors without distance
        return [(v, None) for v in vendors]
    
    vendors_with_distance = []
    filtered_out_count = 0
    
    for vendor in vendors:
        if vendor.latitude and vendor.longitude:
            distance = calculate_distance(
                user_lat, user_lon,
                vendor.latitude, vendor.longitude
            )
            if distance is not None and distance <= max_radius_km:
                vendors_with_distance.append((vendor, distance))
            else:
                filtered_out_count += 1
        else:
            # Vendor without coordinates - include but mark as unknown distance
            vendors_with_distance.append((vendor, None))
    
    # Sort by distance (None values go to end)
    vendors_with_distance.sort(key=lambda x: x[1] if x[1] is not None else float('inf'))
    
    return vendors_with_distance

