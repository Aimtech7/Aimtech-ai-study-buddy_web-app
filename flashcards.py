from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import supabase
from models import Flashcard

flashcards = Blueprint("flashcards", __name__)

@flashcards.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        text = request.form.get("study_text")
        category = request.form.get("category", "General")
        # TODO: Call Hugging Face API to generate Q&A
        question = "Sample Question from AI"
        answer = "Sample Answer from AI"
        
        # Create flashcard in Supabase
        flashcard = Flashcard(
            question=question, 
            answer=answer, 
            user_id=current_user.id,
            category=category,
            mastery_level=0
        )
        flashcard.save()
    
    # Get filter parameters
    filter_category = request.args.get('filter_category', 'all')
    sort_by = request.args.get('sort_by', 'newest')
    
    # Get flashcards from Supabase
    user_flashcards = Flashcard.get_by_user_id(current_user.id, 
                                              category=None if filter_category == 'all' else filter_category,
                                              sort_by=sort_by)
    
    return render_template("dashboard.html", flashcards=user_flashcards)

@flashcards.route("/update-mastery/<int:card_id>", methods=["POST"])
@login_required
def update_mastery(card_id):
    action = request.form.get("mastery")
    
    # Find the flashcard in Supabase
    flashcard = Flashcard.get_by_id(card_id)
    
    if flashcard and flashcard.user_id == current_user.id:
        # Update mastery level
        if action == "increase" and flashcard.mastery_level < 5:
            flashcard.mastery_level += 1
            flash("Great job! Mastery level increased.", "success")
        elif action == "decrease" and flashcard.mastery_level > 0:
            flashcard.mastery_level -= 1
            flash("Keep practicing! Mastery level decreased.", "info")
        
        flashcard.save()
    
    return redirect(url_for('flashcards.dashboard'))
