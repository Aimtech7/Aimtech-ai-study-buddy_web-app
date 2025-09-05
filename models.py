from flask_login import UserMixin
from app import supabase
import json

class User(UserMixin):
    def __init__(self, id=None, email=None, password=None, email_verified=False):
        self.id = id
        self.email = email
        self.password = password
        self.email_verified = email_verified
    
    @staticmethod
    def get_by_email(email):
        """Get user by email from Supabase"""
        if supabase:
            response = supabase.table('users').select('*').eq('email', email).execute()
            if response.data:
                return User.from_supabase(response.data[0])
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID from Supabase"""
        if supabase:
            response = supabase.table('users').select('*').eq('id', user_id).execute()
            if response.data:
                return User.from_supabase(response.data[0])
        return None
    
    @staticmethod
    def from_supabase(data):
        """Convert Supabase user data to User model"""
        return User(
            id=data.get('id'),
            email=data.get('email'),
            password=data.get('password'),
            email_verified=data.get('email_verified', False)
        )
    
    def to_dict(self):
        """Convert User model to dictionary for Supabase"""
        return {
            'email': self.email,
            'password': self.password,
            'email_verified': self.email_verified
        }
    
    def save(self):
        """Save user to Supabase"""
        if not self.id:
            # Create new user
            response = supabase.table('users').insert(self.to_dict()).execute()
            if response.data:
                self.id = response.data[0].get('id')
                return True
        else:
            # Update existing user
            response = supabase.table('users').update(self.to_dict()).eq('id', self.id).execute()
            return bool(response.data)
        return False

class Flashcard:
    def __init__(self, id=None, question=None, answer=None, user_id=None, 
                 category="General", mastery_level=0):
        self.id = id
        self.question = question
        self.answer = answer
        self.user_id = user_id
        self.category = category
        self.mastery_level = mastery_level
    
    @staticmethod
    def get_by_user_id(user_id, category=None, sort_by=None):
        """Get flashcards by user_id from Supabase with optional filtering and sorting"""
        if supabase:
            query = supabase.table('flashcards').select('*').eq('user_id', user_id)
            
            # Apply category filter if provided
            if category and category != "All":
                query = query.eq('category', category)
            
            # Apply sorting if provided
            if sort_by:
                if sort_by == "newest":
                    query = query.order('id', desc=True)
                elif sort_by == "oldest":
                    query = query.order('id', desc=False)
                elif sort_by == "mastery":
                    query = query.order('mastery_level', desc=False)
            
            response = query.execute()
            return [Flashcard.from_supabase(item) for item in response.data]
        return []
    
    @staticmethod
    def get_by_id(card_id):
        """Get flashcard by ID from Supabase"""
        if supabase:
            response = supabase.table('flashcards').select('*').eq('id', card_id).execute()
            if response.data:
                return Flashcard.from_supabase(response.data[0])
        return None
    
    @staticmethod
    def from_supabase(data):
        """Convert Supabase flashcard data to Flashcard model"""
        return Flashcard(
            id=data.get('id'),
            question=data.get('question'),
            answer=data.get('answer'),
            user_id=data.get('user_id'),
            category=data.get('category', 'General'),
            mastery_level=data.get('mastery_level', 0)
        )
    
    def to_dict(self):
        """Convert Flashcard model to dictionary for Supabase"""
        return {
            'question': self.question,
            'answer': self.answer,
            'user_id': self.user_id,
            'category': self.category,
            'mastery_level': self.mastery_level
        }
    
    def save(self):
        """Save flashcard to Supabase"""
        if not self.id:
            # Create new flashcard
            response = supabase.table('flashcards').insert(self.to_dict()).execute()
            if response.data:
                self.id = response.data[0].get('id')
                return True
        else:
            # Update existing flashcard
            response = supabase.table('flashcards').update(self.to_dict()).eq('id', self.id).execute()
            return bool(response.data)
        return False
    
    def delete(self):
        """Delete flashcard from Supabase"""
        if self.id:
            response = supabase.table('flashcards').delete().eq('id', self.id).execute()
            return bool(response.data)
        return False
