import smtplib
import logging

# Fixed import for Python 3.13 compatibility
try:
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
except ImportError:
    # Fallback for older Python versions or import issues
    import email.mime.text
    import email.mime.multipart
    MimeText = email.mime.text.MIMEText
    MimeMultipart = email.mime.multipart.MIMEMultipart

# Optional Twilio import
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Warning: Twilio not available. SMS functionality will be disabled.")

from flask import current_app, flash

class TwoFactorService:
    """Service class for handling 2FA operations"""
    
    @staticmethod
    def send_email_otp(email, name, otp_code):
        """Send OTP via email using Gmail SMTP"""
        try:
            # Email configuration
            smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            sender_email = current_app.config.get('MAIL_USERNAME')
            sender_password = current_app.config.get('MAIL_PASSWORD')
            
            if not sender_email or not sender_password:
                current_app.logger.error("Email credentials not configured")
                return False
            
            # Create message
            message = MimeMultipart("alternative")
            message["Subject"] = "Settle Space - Verification Code"
            message["From"] = sender_email
            message["To"] = email
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Verification Code</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; }}
                    .otp-code {{ background: #28a745; color: white; font-size: 32px; font-weight: bold; 
                               text-align: center; padding: 20px; margin: 20px 0; border-radius: 5px; 
                               letter-spacing: 5px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                    .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏠 Settle Space</h1>
                        <h2>Verification Code</h2>
                    </div>
                    <div class="content">
                        <h3>Hello {name}!</h3>
                        <p>Your verification code is:</p>
                        <div class="otp-code">{otp_code}</div>
                        <div class="warning">
                            <strong>⚠️ Important:</strong>
                            <ul>
                                <li>This code expires in <strong>10 minutes</strong></li>
                                <li>Never share this code with anyone</li>
                                <li>Settle Space will never ask for this code over phone or email</li>
                            </ul>
                        </div>
                        <p>If you didn't request this code, please ignore this email or contact support.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Settle Space | Find Your Perfect Property</p>
                        <p>This is an automated message, please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create text content for email clients that don't support HTML
            text_content = f"""
            Settle Space - Verification Code
            
            Hello {name}!
            
            Your verification code is: {otp_code}
            
            IMPORTANT:
            - This code expires in 10 minutes
            - Never share this code with anyone
            - Settle Space will never ask for this code over phone or email
            
            If you didn't request this code, please ignore this email.
            
            © 2025 Settle Space
            This is an automated message, please do not reply.
            """
            
            # Attach parts
            text_part = MimeText(text_content, "plain")
            html_part = MimeText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            current_app.logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email OTP to {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_sms_otp(phone, name, otp_code):
        """Send OTP via SMS using Twilio - DEBUG VERSION"""
        print(f"=== SMS DEBUG: Starting SMS send to {phone} ===")
        
        if not TWILIO_AVAILABLE:
            print("[ERROR] SMS DEBUG: Twilio not available")
            current_app.logger.error("Twilio not available for SMS")
            return False
            
        try:
            # Twilio configuration
            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            twilio_phone = current_app.config.get('TWILIO_PHONE_NUMBER')
            
            print(f"=== SMS DEBUG: Config check ===")
            print(f"Account SID: {'Set' if account_sid else 'Missing'}")
            print(f"Auth Token: {'Set' if auth_token else 'Missing'}")
            print(f"Twilio Phone: {twilio_phone if twilio_phone else 'Missing'}")
            
            if not all([account_sid, auth_token, twilio_phone]):
                print("[ERROR] SMS DEBUG: Missing Twilio credentials")
                current_app.logger.error("Twilio credentials not configured")
                return False
            
            # Initialize Twilio client
            client = Client(account_sid, auth_token)
            print("[INFO] SMS DEBUG: Twilio client initialized")
            
            # Format phone number
            original_phone = phone
            clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            
            if not clean_phone.startswith('+'):
                if clean_phone.startswith('91'):
                    formatted_phone = '+' + clean_phone
                elif len(clean_phone) == 10:
                    formatted_phone = '+91' + clean_phone
                else:
                    formatted_phone = '+91' + clean_phone
            else:
                formatted_phone = clean_phone
            
            print(f"=== SMS DEBUG: Phone formatting ===")
            print(f"Original: {original_phone}")
            print(f"Cleaned: {clean_phone}")
            print(f"Formatted: {formatted_phone}")
            
            # Create message
            message_body = f"Your Settle Space verification code is: {otp_code}\n\nThis code expires in 10 minutes."
            
            print(f"=== SMS DEBUG: Sending message ===")
            print(f"From: {twilio_phone}")
            print(f"To: {formatted_phone}")
            print(f"Message: {message_body}")
            
            # Send SMS
            message = client.messages.create(
                body=message_body,
                from_=twilio_phone,
                to=formatted_phone
            )
            
            print(f"[INFO] SMS DEBUG: Message sent!")
            print(f"Message SID: {message.sid}")
            print(f"Status: {message.status}")
            print(f"Direction: {message.direction}")
            print(f"Error Code: {message.error_code}")
            print(f"Error Message: {message.error_message}")
            
            current_app.logger.info(f"OTP SMS sent to {formatted_phone}, SID: {message.sid}")
            return True
            
        except Exception as e:
            print(f"[ERROR] SMS DEBUG: Error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            current_app.logger.error(f"Failed to send SMS OTP to {phone}: {str(e)}")
            return False
    
    @staticmethod
    def send_otp(user, method='email'):
        """Send OTP using specified method"""
        try:
            # Generate OTP
            otp_code = user.generate_otp(method)
            
            if method == 'email':
                success = TwoFactorService.send_email_otp(user.email, user.name, otp_code)
                if success:
                    flash(f'Verification code sent to your email: {user.email[:3]}***@{user.email.split("@")[1]}', 'info')
                else:
                    flash('Failed to send email verification. Please try SMS instead.', 'error')
                return success
                
            elif method == 'sms':
                success = TwoFactorService.send_sms_otp(user.phone, user.name, otp_code)
                if success:
                    masked_phone = user.phone[:3] + '*' * (len(user.phone) - 6) + user.phone[-3:]
                    flash(f'Verification code sent to your phone: {masked_phone}', 'info')
                else:
                    flash('Failed to send SMS verification. Please try email instead.', 'error')
                return success
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error sending OTP to user {user.id}: {str(e)}")
            flash('Failed to send verification code. Please try again.', 'error')
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after successful registration"""
        try:
            smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            sender_email = current_app.config.get('MAIL_USERNAME')
            sender_password = current_app.config.get('MAIL_PASSWORD')
            
            if not sender_email or not sender_password:
                return False
            
            message = MimeMultipart("alternative")
            message["Subject"] = "Welcome to Settle Space!"
            message["From"] = sender_email
            message["To"] = user.email
            
            role_specific_content = {
                'customer': {
                    'welcome_msg': 'Welcome to Settle Space! Start exploring amazing properties.',
                    'features': [
                        'Browse thousands of verified properties',
                        'Save your favorite properties',
                        'Send direct inquiries to property owners',
                        'Get personalized property recommendations'
                    ]
                },
                'seller': {
                    'welcome_msg': 'Welcome to Settle Space! Start listing your properties.',
                    'features': [
                        'List unlimited properties',
                        'Receive direct inquiries from buyers',
                        'Manage all your listings in one place',
                        'Track payment status and approvals'
                    ]
                }
            }
            
            content = role_specific_content.get(user.role, role_specific_content['customer'])
            features_html = ''.join([f'<li>{feature}</li>' for feature in content['features']])
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Welcome to Settle Space</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; 
                               padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .features {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .cta-button {{ background: #28a745; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block; 
                                  margin: 20px 0; font-weight: bold; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏠 Welcome to Settle Space!</h1>
                        <h2>Hello {user.name}!</h2>
                    </div>
                    <div class="content">
                        <p>{content['welcome_msg']}</p>
                        <div class="features">
                            <h3>What you can do:</h3>
                            <ul>{features_html}</ul>
                        </div>
                        <div style="text-align: center;">
                            <a href="{current_app.config.get('SERVER_URL', 'http://localhost:5000')}/login" 
                               class="cta-button">Login to Your Account</a>
                        </div>
                        <p>Need help? Our support team is always here to assist you.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Settle Space | Find Your Perfect Property</p>
                        <p>This is an automated message, please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_part = MimeText(html_content, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False