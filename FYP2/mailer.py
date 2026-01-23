import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
# Your verified FYP credentials
SENDER_EMAIL = "limzhihao0513@gmail.com"
APP_PASSWORD = "xugmqgryoxqowiez" # 16-character Google App Password with no spaces

def send_verification_email(receiver_email, token):
    """Sends a professional verification link for new account registration."""
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify Your Kemaslah Account"
    message["From"] = f"Kemaslah Manager <{SENDER_EMAIL}>"
    message["To"] = receiver_email

    verify_url = f"http://127.0.0.1:5000/verify?token={token}"

    html = f"""
    <html>
      <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #0B1426; color: white;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0B1426; padding: 40px 20px;">
          <tr>
            <td align="center">
              <table width="400" border="0" cellspacing="0" cellpadding="0" style="background-color: #1A202C; border-radius: 25px; padding: 40px; text-align: center;">
                <tr>
                  <td>
                    <h1 style="color: #FFFFFF; font-size: 24px; margin-bottom: 10px;">Welcome to Kemaslah</h1>
                    <p style="color: #718096; font-size: 14px; margin-bottom: 30px;">Your smarter file manager</p>
                    <p style="color: #CBD5E0; font-size: 16px; line-height: 1.5;">Please verify your email address to complete registration:</p>
                    <div style="margin: 30px 0;">
                        <a href="{verify_url}" style="display: inline-block; background-color: #0D3B66; color: #FFFFFF; padding: 12px 35px; font-weight: bold; text-decoration: none; border-radius: 22px; font-size: 14px;">Verify Email</a>
                    </div>
                    <p style="color: #718096; font-size: 11px; margin-top: 40px;">If you didn't request this email, you can safely ignore it.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))
    return _execute_send(receiver_email, message)

def send_otp_email(receiver_email, otp_code):
    """Sends a 6-digit OTP code for password reset requests."""
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Kemaslah Password Reset Code"
    message["From"] = f"Kemaslah Security <{SENDER_EMAIL}>"
    message["To"] = receiver_email

    # Professional OTP Template matching Figma colors
    html = f"""
    <html>
      <body style="margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background-color: #0B1426; color: white;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0B1426; padding: 40px 20px;">
          <tr>
            <td align="center">
              <table width="400" border="0" cellspacing="0" cellpadding="0" style="background-color: #1A202C; border-radius: 25px; padding: 40px; text-align: center;">
                <tr>
                  <td>
                    <h1 style="color: #FFFFFF; font-size: 24px; margin-bottom: 10px;">Reset Your Password</h1>
                    <p style="color: #718096; font-size: 14px; margin-bottom: 30px;">Security Verification</p>
                    <p style="color: #CBD5E0; font-size: 16px;">Use the 6-digit code below to reset your password:</p>
                    
                    <div style="margin: 30px 0; background-color: #0B1426; padding: 20px; border-radius: 15px; border: 1px solid #2D3748;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #3182CE;">{otp_code}</span>
                    </div>

                    <p style="color: #718096; font-size: 11px; margin-top: 40px;">This code will expire shortly. If you did not request a password reset, please secure your account.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))
    return _execute_send(receiver_email, message)

def _execute_send(receiver_email, message):
    """Internal helper to handle the SMTP connection logic."""
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())
        return True
    except Exception as e:
        raise e

if __name__ == "__main__":
    # Test line: send_otp_email("your-test-email@example.com", "123456")
    pass