from flask import Flask, render_template
from flask_login import LoginManager
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

login_manager = LoginManager()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

def init_supabase_tables():
    """Initialize Supabase tables if they don't exist"""
    if not supabase:
        print("Supabase client not configured. Skipping table initialization.")
        return
    
    try:
        # Create users table if it doesn't exist
        try:
            supabase.table('users').select('count').limit(1).execute()
            print("Users table exists")
        except Exception:
            print("Creating users table...")
            supabase.sql("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(200) NOT NULL,
                    email_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """).execute()
        
        # Create flashcards table if it doesn't exist
        try:
            supabase.table('flashcards').select('count').limit(1).execute()
            print("Flashcards table exists")
        except Exception:
            print("Creating flashcards table...")
            supabase.sql("""
                CREATE TABLE IF NOT EXISTS flashcards (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    category VARCHAR(50) DEFAULT 'General',
                    mastery_level INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """).execute()
        
        print("Supabase tables initialized successfully!")
    except Exception as e:
        print(f"Error initializing Supabase tables: {e}")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.get_by_id(user_id)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev_secret")
    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from auth import auth as auth_blueprint
    from flashcards import flashcards as flashcards_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(flashcards_blueprint)

    @app.route('/')
    def index():
        return render_template("index.html")
    
    # Initialize Supabase tables
    with app.app_context():
        init_supabase_tables()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, use_reloader=False)
