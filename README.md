# Aimtech – AI Study Buddy (with Authentication & Database)

This project is an **AI-powered flashcard generator** built for education (Hackathon 2025, SDG4).  
It includes **user authentication, database persistence, and AI-generated flashcards**.

---

## 📌 Project Prompt (for reference)

Build a complete project called **“Aimtech – AI Study Buddy”**, an AI-powered flashcard generator for education.  

### 🔹 Requirements
- Flask backend with authentication (Flask-Login)
- Supabase for database and authentication
- Hugging Face API integration for flashcard generation
- Flashcards saved per user in Supabase
- Deployment ready for Render + Heroku
- GitHub Actions workflows for CI/CD
- Documentation included

---

## 📂 Project Structure

```
.
├── app.py
├── models.py
├── auth.py
├── flashcards.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── static/
│   ├── style.css
│   └── logo.svg
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
├── .env.example
├── .github/workflows/
│   ├── deploy-render.yml
│   └── deploy-heroku.yml
└── README.md
```

---
# Aimtech-ai-study-buddy_web-app
