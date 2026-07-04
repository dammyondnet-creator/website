# server.py - Complete Python Flask Backend for D1 Streams

import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='.')
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///d1streams.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
EMAIL_USER = os.environ.get('EMAIL_USER', 'dammyondnet@gmail.com')
EMAIL_PASS = os.environ.get('EMAIL_PASS', '')  # Use App Password for Gmail
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'dammyondnet@gmail.com')

# Initialize database
db = SQLAlchemy(app)

# ============================================
# DATABASE MODELS
# ============================================

class Booking(db.Model):
    """Booking model for storing client bookings"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_category = db.Column(db.String(50), nullable=False)
    package_name = db.Column(db.String(100))
    package_id = db.Column(db.String(50))
    num_sessions = db.Column(db.Integer, default=1)
    session_dates = db.Column(db.Text)  # JSON array of dates
    payment_method = db.Column(db.String(50))
    total_amount = db.Column(db.Float, default=0)
    discount_applied = db.Column(db.Boolean, default=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'package_name': self.package_name,
            'package_id': self.package_id,
            'num_sessions': self.num_sessions,
            'session_dates': json.loads(self.session_dates) if self.session_dates else [],
            'payment_method': self.payment_method,
            'total_amount': self.total_amount,
            'discount_applied': self.discount_applied,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class Feedback(db.Model):
    """Feedback model for storing client feedback"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rating': self.rating,
            'message': self.message,
            'createdAt': self.created_at.isoformat()
        }

# ============================================
# EMAIL FUNCTIONS
# ============================================

def send_email(to_email, subject, body_html, body_text=None):
    """Send email using SMTP"""
    if not EMAIL_PASS:
        logger.warning("EMAIL_PASS not set. Email will not be sent.")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        
        if body_text:
            text_part = MIMEText(body_text, 'plain')
            msg.attach(text_part)
        
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_client_confirmation(booking_data):
    """Send booking confirmation email to client"""
    session_details = ""
    if booking_data.get('num_sessions', 1) > 1:
        session_details = "<h4>📅 Session Dates:</h4><ul>"
        for i, date in enumerate(booking_data.get('session_dates', [])):
            session_details += f"<li>Session {i+1}: {date}</li>"
        session_details += "</ul>"
    else:
        dates = booking_data.get('session_dates', [])
        session_details = f"<p><strong>📅 Date:</strong> {dates[0] if dates else 'To be confirmed'}</p>"
    
    discount_msg = ""
    if booking_data.get('discount_applied', False):
        discount_msg = "<p>🎉 <strong>10% multi-session discount applied!</strong></p>"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #4a6cf7, #7c5cfc); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .detail {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
            .highlight {{ color: #4a6cf7; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Booking Confirmed!</h1>
                <p>Thank you for choosing D1 Streams</p>
            </div>
            <div class="content">
                <h2>Dear {booking_data.get('name')},</h2>
                <p>Thank you for booking with <strong>D1 Streams</strong>! 🙏</p>
                <p>We are excited to work with you on your upcoming event.</p>
                
                <h3>📋 Booking Details:</h3>
                <div class="detail">
                    <p><strong>👤 Name:</strong> {booking_data.get('name')}</p>
                    <p><strong>📧 Email:</strong> {booking_data.get('email')}</p>
                    <p><strong>🎬 Service:</strong> {booking_data.get('event_type', '').replace('-', ' ').upper()}</p>
                    <p><strong>🏷️ Event:</strong> {booking_data.get('event_category', '').replace('-', ' ').upper()}</p>
                    <p><strong>📦 Package:</strong> {booking_data.get('package_name', 'Not specified')}</p>
                    <p><strong>📅 Sessions:</strong> {booking_data.get('num_sessions', 1)}</p>
                    {session_details}
                    <p><strong>💳 Payment:</strong> {booking_data.get('payment_method', '').upper()}</p>
                    <p><strong>💰 Total:</strong> £{booking_data.get('total_amount', 0):.2f}</p>
                    {discount_msg}
                </div>
                
                <p><strong>📝 Special Requirements:</strong> {booking_data.get('message', 'None')}</p>
                
                <p style="margin-top: 20px;">Our team will review your requirements and get back to you within 24 hours.</p>
                
                <p>If you have any urgent questions, please reply to this email or contact us at <a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a></p>
                
                <p style="margin-top: 30px;">We look forward to making your event a success! 🎥✨</p>
                
                <p><strong>Best regards,</strong><br>The D1 Streams Team</p>
            </div>
            <div class="footer">
                <p>© 2026 D1 Streams — live streaming & recording studio</p>
                <p><a href="https://d1streams.com">www.d1streams.com</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Booking Confirmation - D1 Streams

Dear {booking_data.get('name')},

Thank you for booking with D1 Streams!

Booking Details:
------------------------
Name: {booking_data.get('name')}
Email: {booking_data.get('email')}
Service: {booking_data.get('event_type', '').replace('-', ' ').upper()}
Event: {booking_data.get('event_category', '').replace('-', ' ').upper()}
Package: {booking_data.get('package_name', 'Not specified')}
Sessions: {booking_data.get('num_sessions', 1)}
Payment: {booking_data.get('payment_method', '').upper()}
Total: £{booking_data.get('total_amount', 0):.2f}

Special Requirements: {booking_data.get('message', 'None')}

Our team will review your requirements and get back to you within 24 hours.

We look forward to making your event a success!

Best regards,
The D1 Streams Team
"""
    
    return send_email(
        to_email=booking_data.get('email'),
        subject="✅ Booking Confirmation - D1 Streams",
        body_html=html_body,
        body_text=text_body
    )

def send_admin_notification(booking_data):
    """Send booking notification email to admin"""
    session_details = ""
    if booking_data.get('num_sessions', 1) > 1:
        session_details = "<h4>📅 Session Dates:</h4><ul>"
        for i, date in enumerate(booking_data.get('session_dates', [])):
            session_details += f"<li>Session {i+1}: {date}</li>"
        session_details += "</ul>"
    else:
        dates = booking_data.get('session_dates', [])
        session_details = f"<p><strong>📅 Date:</strong> {dates[0] if dates else 'To be confirmed'}</p>"
    
    discount_msg = ""
    if booking_data.get('discount_applied', False):
        discount_msg = "<p>🎉 <strong>10% multi-session discount applied!</strong></p>"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #ff4d6d, #ff8c5a); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .detail {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 New Booking Request</h1>
                <p>Action Required</p>
            </div>
            <div class="content">
                <h2>📋 Booking Details:</h2>
                <div class="detail">
                    <p><strong>👤 Name:</strong> {booking_data.get('name')}</p>
                    <p><strong>📧 Email:</strong> {booking_data.get('email')}</p>
                    <p><strong>🎬 Service:</strong> {booking_data.get('event_type', '').replace('-', ' ').upper()}</p>
                    <p><strong>🏷️ Event:</strong> {booking_data.get('event_category', '').replace('-', ' ').upper()}</p>
                    <p><strong>📦 Package:</strong> {booking_data.get('package_name', 'Not specified')}</p>
                    <p><strong>📅 Sessions:</strong> {booking_data.get('num_sessions', 1)}</p>
                    {session_details}
                    <p><strong>💳 Payment:</strong> {booking_data.get('payment_method', '').upper()}</p>
                    <p><strong>💰 Total:</strong> £{booking_data.get('total_amount', 0):.2f}</p>
                    {discount_msg}
                </div>
                
                <p><strong>📝 Special Requirements:</strong> {booking_data.get('message', 'None')}</p>
                
                <p style="margin-top: 20px;">
                    <a href="mailto:{booking_data.get('email')}" style="background: #4a6cf7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Reply to {booking_data.get('name')}
                    </a>
                </p>
                
                <p style="margin-top: 20px;">Please review and confirm availability.</p>
            </div>
            <div class="footer">
                <p>D1 Streams System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
New Booking Request - D1 Streams

Booking Details:
------------------------
Name: {booking_data.get('name')}
Email: {booking_data.get('email')}
Service: {booking_data.get('event_type', '').replace('-', ' ').upper()}
Event: {booking_data.get('event_category', '').replace('-', ' ').upper()}
Package: {booking_data.get('package_name', 'Not specified')}
Sessions: {booking_data.get('num_sessions', 1)}
Payment: {booking_data.get('payment_method', '').upper()}
Total: £{booking_data.get('total_amount', 0):.2f}

Special Requirements: {booking_data.get('message', 'None')}

Please review and confirm availability.
"""
    
    return send_email(
        to_email=ADMIN_EMAIL,
        subject="🎬 New Booking Request - D1 Streams",
        body_html=html_body,
        body_text=text_body
    )

# ============================================
# API ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings (admin use)"""
    try:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        return jsonify([b.to_dict() for b in bookings])
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        return jsonify({'error': 'Failed to fetch bookings'}), 500

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'email', 'eventType', 'eventCategory']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create booking record
        booking = Booking(
            name=data.get('name'),
            email=data.get('email'),
            event_type=data.get('eventType'),
            event_category=data.get('eventCategory'),
            package_name=data.get('packageName'),
            package_id=data.get('packageId'),
            num_sessions=data.get('numSessions', 1),
            session_dates=json.dumps(data.get('sessionDates', [])),
            payment_method=data.get('paymentMethod', 'card'),
            total_amount=data.get('totalAmount', 0),
            discount_applied=data.get('discountApplied', False),
            message=data.get('message', ''),
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Prepare booking data for email
        booking_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'event_type': data.get('eventType'),
            'event_category': data.get('eventCategory'),
            'package_name': data.get('packageName'),
            'package_id': data.get('packageId'),
            'num_sessions': data.get('numSessions', 1),
            'session_dates': data.get('sessionDates', []),
            'payment_method': data.get('paymentMethod', 'card'),
            'total_amount': data.get('totalAmount', 0),
            'discount_applied': data.get('discountApplied', False),
            'message': data.get('message', '')
        }
        
        # Send emails
        send_client_confirmation(booking_data)
        send_admin_notification(booking_data)
        
        return jsonify({
            'success': True,
            'message': 'Booking created successfully',
            'booking': booking.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """Get all feedback"""
    try:
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
        return jsonify([f.to_dict() for f in feedbacks])
    except Exception as e:
        logger.error(f"Error fetching feedback: {str(e)}")
        return jsonify({'error': 'Failed to fetch feedback'}), 500

@app.route('/api/feedback', methods=['POST'])
def create_feedback():
    """Create new feedback"""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('message'):
            return jsonify({'error': 'Name and message are required'}), 400
        
        feedback = Feedback(
            name=data.get('name'),
            rating=data.get('rating', 5),
            message=data.get('message')
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully',
            'feedback': feedback.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating feedback: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/clear', methods=['DELETE'])
def clear_bookings():
    """Clear all bookings (admin use)"""
    try:
        deleted = Booking.query.delete()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted} bookings'
        })
    except Exception as e:
        logger.error(f"Error clearing bookings: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================
# INITIALIZATION
# ============================================

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)