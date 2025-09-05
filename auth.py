from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import login_manager, supabase
from models import User
import json
import secrets
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

auth = Blueprint("auth", __name__)

# Create serializer for tokens
serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'dev-key'))

def send_email(to, subject, template):
    """Helper function to send emails"""
    # This is a placeholder - in production, use a proper email service
    # like SendGrid, Mailgun, AWS SES, etc.
    try:
        # For development, just print the email content
        print(f"Email to: {to}")
        print(f"Subject: {subject}")
        print(f"Content: {template}")
        
        # In production, uncomment and configure this code:
        """
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = 'your-email@example.com'
        msg['To'] = to
        
        msg.attach(MIMEText(template, 'html'))
        
        server = smtplib.SMTP('smtp.example.com', 587)
        server.starttls()
        server.login('your-email@example.com', 'your-password')
        server.send_message(msg)
        server.quit()
        """
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@login_manager.user_loader
def load_user(user_id):
    # Get user from Supabase
    if supabase:
        # Try to get from Supabase users table
        user = User.get_by_id(int(user_id))
        if user:
            return user
        
        # If user has a Supabase Auth session, try to get user info
        if 'supabase_session' in session:
            try:
                user_response = supabase.auth.get_user(session['supabase_session'])
                if user_response and user_response.user:
                    # Create a User object from Supabase Auth user
                    user_data = {
                        'id': user_response.user.id,
                        'email': user_response.user.email,
                        'password': 'supabase_auth_user'  # Placeholder as we don't store passwords
                    }
                    return User(**user_data)
            except Exception as e:
                print(f"Error getting Supabase Auth user: {e}")
    
    return None

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Try to get user from Supabase
        user = User.get_by_email(email)
        
        # If not found, try Supabase Auth
        if not user and supabase:
            try:
                # Sign in with Supabase Auth
                auth_response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if auth_response.user:
                    # Store Supabase session
                    session['supabase_session'] = auth_response.session.access_token
                    
                    # Create a User object from Supabase Auth user
                    user_data = {
                        'id': auth_response.user.id,
                        'email': auth_response.user.email,
                        'password': generate_password_hash('supabase_auth_user', method="sha256"),
                        'email_verified': True  # Assume verified for Supabase Auth users
                    }
                    user = User(**user_data)
                    
                    # Also add to Supabase database for future reference
                    user.save()
            except Exception as e:
                print(f"Supabase Auth error: {e}")
                flash("Invalid login credentials")
            
        if user and (password == 'supabase_auth_user' or check_password_hash(user.password, password)):
            # Check if email is verified
            if not user.email_verified:
                flash("Please verify your email before logging in.")
                return redirect(url_for("auth.verify_email", email=email))
            
            login_user(user)
            return redirect(url_for("flashcards.dashboard"))
        else:
            flash("Invalid login credentials")
    return render_template("login.html")

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_pw = generate_password_hash(password, method="sha256")
        
        # Check if user already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            flash("Email already registered. Please login.")
            return redirect(url_for("auth.login"))
        
        # Create user in Supabase with email_verified=False
        new_user = User(
            email=email, 
            password=hashed_pw, 
            email_verified=False
        )
        new_user.save()
        
        # Generate verification token
        token = serializer.dumps(email, salt='email-verification')
        
        # Create verification link
        verification_url = url_for('auth.verify_token', token=token, _external=True)
        
        # Send verification email
        email_template = f"""
        <h1>Verify Your Email</h1>
        <p>Thank you for registering! Please click the link below to verify your email:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>This link will expire in 24 hours.</p>
        """
        
        send_email(email, "Verify Your Email", email_template)
        
        # If Supabase Auth is configured, also create user there
        if supabase:
            try:
                # Create user in Supabase Auth
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
            except Exception as e:
                print(f"Supabase registration error: {e}")
        
        return redirect(url_for("auth.verify_email", email=email))
    return render_template("register.html")

@auth.route("/verify-email")
def verify_email():
    email = request.args.get("email", "")
    return render_template("verify_email.html", email=email)

@auth.route("/verify-token/<token>")
def verify_token(token):
    try:
        # Verify token with 24-hour expiration
        email = serializer.loads(token, salt='email-verification', max_age=86400)
        
        # Update user's email_verified status
        user = User.get_by_email(email)
        if user:
            user.email_verified = True
            user.save()
            
            flash("Email verified successfully! You can now login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("User not found.", "error")
            return redirect(url_for("auth.login"))
    except SignatureExpired:
        flash("The verification link has expired. Please request a new one.", "error")
        return redirect(url_for("auth.verify_email"))
    except Exception as e:
        flash("Invalid verification link.", "error")
        return redirect(url_for("auth.verify_email"))

@auth.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email", "")
    if not email:
        flash("Email address is required.", "error")
        return redirect(url_for("auth.verify_email"))
    
    # Generate new verification token
    token = serializer.dumps(email, salt='email-verification')
    
    # Create verification link
    verification_url = url_for('auth.verify_token', token=token, _external=True)
    
    # Send verification email
    email_template = f"""
    <h1>Verify Your Email</h1>
    <p>Thank you for registering! Please click the link below to verify your email:</p>
    <p><a href="{verification_url}">Verify Email</a></p>
    <p>This link will expire in 24 hours.</p>
    """
    
    if send_email(email, "Verify Your Email", email_template):
        flash("Verification email sent. Please check your inbox.", "success")
    else:
        flash("Failed to send verification email. Please try again later.", "error")
    
    return redirect(url_for("auth.verify_email", email=email))

@auth.route("/profile", methods=["GET", "POST"])
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    
    # Get user's flashcard count
    from models import Flashcard
    flashcard_count = Flashcard.get_by_user_id(current_user.id).count()
    
    # Get creation date (placeholder - in a real app, store this in the user model)
    created_at = "N/A"
    
    if request.method == "POST":
        email = request.form.get("email")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # Verify current password
        if not check_password_hash(current_user.password, current_password):
            flash("Current password is incorrect.")
            return redirect(url_for("auth.profile"))
        
        # Update email if changed
        if email != current_user.email:
            # Check if email is already in use
            existing_user = User.get_by_email(email)
            if existing_user and existing_user.id != current_user.id:
                flash("Email is already in use.")
                return redirect(url_for("auth.profile"))
            
            current_user.email = email
            current_user.email_verified = False
            
            # Generate verification token for new email
            token = serializer.dumps(email, salt='email-verification')
            verification_url = url_for('auth.verify_token', token=token, _external=True)
            
            # Send verification email
            email_template = f"""
            <h1>Verify Your New Email</h1>
            <p>Please click the link below to verify your new email address:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            """
            
            send_email(email, "Verify Your New Email", email_template)
            flash("Email updated. Please verify your new email address.")
        
        # Update password if provided
        if new_password:
            if new_password != confirm_password:
                flash("New passwords don't match.")
                return redirect(url_for("auth.profile"))
            
            current_user.password = generate_password_hash(new_password, method="sha256")
            flash("Password updated successfully.")
            
            # Update in Supabase Auth if configured
            if supabase:
                try:
                    # Update password in Supabase Auth
                    supabase.auth.update_user({
                        "password": new_password
                    })
                except Exception as e:
                    print(f"Supabase Auth update error: {e}")
        
        # Save changes to Supabase
        current_user.save()
        flash("Profile updated successfully.")
        return redirect(url_for("auth.profile"))
    
    return render_template("profile.html", user=current_user, flashcard_count=flashcard_count, created_at=created_at)

@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.get_by_email(email)
        
        if user:
            # Generate token
            token = secrets.token_urlsafe(32)
            expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
            
            # Store token in session (in production, use a database)
            session['reset_tokens'] = session.get('reset_tokens', {})
            session['reset_tokens'][token] = {
                'email': email,
                'expiry': expiry.isoformat()
            }
            
            # Create reset link
            reset_url = url_for('auth.reset_password_confirm', token=token, _external=True)
            
            # Send email with reset link
            email_template = f"""
            <h1>Reset Your Password</h1>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            """
            
            send_email(email, "Password Reset Request", email_template)
            
            # If Supabase Auth is configured, use their password reset
            if supabase:
                try:
                    supabase.auth.reset_password_email(email)
                except Exception as e:
                    print(f"Supabase password reset error: {e}")
                    # Fall back to our custom reset link
            
            # In a real app, send email with reset link
            reset_url = url_for('auth.reset_password_confirm', token=token, _external=True)
            print(f"Password reset link (would be emailed): {reset_url}")
            
        # Always show success to prevent email enumeration
        flash("If your email is registered, you will receive a password reset link shortly.")
        return redirect(url_for("auth.login"))
    
    return render_template("reset_password.html")

@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_confirm(token):
    # Check if token is valid
    reset_tokens = session.get('reset_tokens', {})
    token_data = reset_tokens.get(token)
    
    if not token_data:
        flash("Invalid or expired reset link.")
        return redirect(url_for("auth.login"))
    
    # Check if token is expired
    expiry = datetime.datetime.fromisoformat(token_data['expiry'])
    if datetime.datetime.now() > expiry:
        # Remove expired token
        reset_tokens.pop(token, None)
        session['reset_tokens'] = reset_tokens
        
        flash("Reset link has expired. Please request a new one.")
        return redirect(url_for("auth.reset_password"))
    
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            flash("Passwords don't match.")
            return redirect(url_for("auth.reset_password_confirm", token=token))
        
        # Update password
        email = token_data['email']
        user = User.get_by_email(email)
        
        if user:
            # Update password in Supabase
            user.password = generate_password_hash(password, method="sha256")
            user.save()
            
            # Update in Supabase Auth if configured
            if supabase:
                try:
                    # Try to update password in Supabase Auth
                    # Note: This might require the user to be logged in
                    supabase.auth.update_user({
                        "password": password
                    })
                except Exception as e:
                    print(f"Supabase Auth update error: {e}")
            
            # Remove used token
            reset_tokens.pop(token, None)
            session['reset_tokens'] = reset_tokens
            
            flash("Password has been reset successfully.")
            return redirect(url_for("auth.login"))
        else:
            flash("User not found.")
            return redirect(url_for("auth.login"))
    
    return render_template("reset_password_confirm.html")






@auth.route("/logout")
@login_required
def logout():
    # Clear Supabase session if exists
    if 'supabase_session' in session:
        try:
            supabase.auth.sign_out()
            session.pop('supabase_session')
        except Exception as e:
            print(f"Error signing out from Supabase: {e}")
    
    logout_user()
    return redirect(url_for("auth.login"))
