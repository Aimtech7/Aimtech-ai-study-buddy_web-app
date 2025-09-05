from app import supabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_supabase():
    """Initialize Supabase tables and policies"""
    if not supabase:
        print("Supabase client not configured. Please check your environment variables.")
        return False
    
    try:
        # Create users table if it doesn't exist
        supabase.table('users').select('count').limit(1).execute()
    except Exception:
        print("Creating users table...")
        # Using raw SQL to create the table with proper constraints
        supabase.sql("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(200) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """).execute()
    
    try:
        # Create flashcards table if it doesn't exist
        supabase.table('flashcards').select('count').limit(1).execute()
    except Exception:
        print("Creating flashcards table...")
        # Using raw SQL to create the table with proper constraints
        supabase.sql("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """).execute()
    
    # Set up Row Level Security (RLS) policies
    try:
        # Enable RLS on tables
        supabase.sql("ALTER TABLE users ENABLE ROW LEVEL SECURITY;").execute()
        supabase.sql("ALTER TABLE flashcards ENABLE ROW LEVEL SECURITY;").execute()
        
        # Create policies for users table
        supabase.sql("""
            CREATE POLICY IF NOT EXISTS "Users can view their own data" 
            ON users FOR SELECT 
            USING (auth.uid()::text = id::text);
        """).execute()
        
        # Create policies for flashcards table
        supabase.sql("""
            CREATE POLICY IF NOT EXISTS "Users can view their own flashcards" 
            ON flashcards FOR SELECT 
            USING (auth.uid()::text = user_id::text);
            
            CREATE POLICY IF NOT EXISTS "Users can insert their own flashcards" 
            ON flashcards FOR INSERT 
            WITH CHECK (auth.uid()::text = user_id::text);
            
            CREATE POLICY IF NOT EXISTS "Users can update their own flashcards" 
            ON flashcards FOR UPDATE
            USING (auth.uid()::text = user_id::text);
            
            CREATE POLICY IF NOT EXISTS "Users can delete their own flashcards" 
            ON flashcards FOR DELETE
            USING (auth.uid()::text = user_id::text);
        """).execute()
        
        print("Supabase tables and policies created successfully!")
        return True
    except Exception as e:
        print(f"Error setting up RLS policies: {e}")
        return False

if __name__ == "__main__":
    init_supabase()