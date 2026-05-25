from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import re
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ========== USER TABLE ==========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# ========== QUIZ TABLE ==========
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200))
    option1 = db.Column(db.String(100))
    option2 = db.Column(db.String(100))
    option3 = db.Column(db.String(100))
    answer = db.Column(db.String(100))

# ========== LEADERBOARD TABLE ==========
class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    score = db.Column(db.Integer)

# ========== ROUTES ==========
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

# ========== DASHBOARD ROUTE (NEW ADDED) ==========
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ========== PHISHING DETECTOR ==========
blacklist = ['fake', 'login-free', 'hack']

@app.route('/phishing', methods=['GET', 'POST'])
def phishing():
    result = ""
    if request.method == 'POST':
        url = request.form['url']
        for word in blacklist:
            if word in url:
                result = "Phishing URL Detected!"
                break
        else:
            result = "Safe URL"
    return render_template('phishing.html', result=result)

# ========== BREACH CHECKER ==========
breached_emails = [
    'test@gmail.com',
    'admin@gmail.com'
]

@app.route('/breach', methods=['GET', 'POST'])
def breach():
    result = ""
    if request.method == 'POST':
        email = request.form['email']
        if email in breached_emails:
            result = "Email Found in Data Breach!"
        else:
            result = "Safe Email"
    return render_template('breach.html', result=result)

# ========== PASSWORD ANALYZER ==========
@app.route('/password', methods=['GET', 'POST'])
def password():
    strength = ""
    if request.method == 'POST':
        password = request.form['password']
        if len(password) < 6:
            strength = "Weak"
        elif re.search("[A-Z]", password) and re.search("[0-9]", password):
            strength = "Strong"
        else:
            strength = "Medium"
    return render_template('password.html', strength=strength)

# ========== QUIZ SYSTEM ==========
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    questions = Quiz.query.all()
    
    if not questions:
        return "No questions in database! Add some questions first."
    
    if request.method == 'POST':
        selected_answer = request.form['answer']
        correct_answer = request.form['correct_answer']
        
        if selected_answer == correct_answer:
            result = "Correct! 🎉"
        else:
            result = f"Wrong! Correct answer was: {correct_answer}"
        
        question = random.choice(questions)
        return render_template('quiz.html', question=question, result=result)
    
    question = random.choice(questions)
    return render_template('quiz.html', question=question, result="")

# ========== LEADERBOARD ==========
@app.route('/leaderboard')
def leaderboard():
    top_scores = Leaderboard.query.order_by(Leaderboard.score.desc()).limit(10).all()
    return render_template('leaderboard.html', scores=top_scores)

@app.route('/save_score', methods=['POST'])
def save_score():
    username = session.get('username', 'Anonymous')
    score = request.form.get('score', 0)
    
    entry = Leaderboard(username=username, score=int(score))
    db.session.add(entry)
    db.session.commit()
    
    return redirect('/leaderboard')

# ========== CAESAR CIPHER ==========
def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            shift_base = 65 if char.isupper() else 97
            result += chr((ord(char) - shift_base + shift) % 26 + shift_base)
        else:
            result += char
    return result

def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)

@app.route('/cipher', methods=['GET', 'POST'])
def cipher():
    result = ""
    if request.method == 'POST':
        message = request.form['message']
        shift = int(request.form['shift'])
        action = request.form['action']
        
        if action == 'encrypt':
            result = caesar_encrypt(message, shift)
        else:
            result = caesar_decrypt(message, shift)
    
    return render_template('cipher.html', result=result)

# ========== ADD SAMPLE QUESTIONS ==========
def add_sample_questions():
    questions = [
        {
            'question': 'What does "Phishing" refer to in cybersecurity?',
            'option1': 'Fishing for compliments',
            'option2': 'Fake emails/websites to steal data',
            'option3': 'A type of computer virus',
            'answer': 'Fake emails/websites to steal data'
        },
        {
            'question': 'What is a strong password?',
            'option1': '123456',
            'option2': 'password',
            'option3': 'Mix of uppercase, lowercase, numbers & symbols',
            'answer': 'Mix of uppercase, lowercase, numbers & symbols'
        },
        {
            'question': 'What does 2FA stand for?',
            'option1': 'Two Factor Authentication',
            'option2': 'Second File Access',
            'option3': 'Dual Password System',
            'answer': 'Two Factor Authentication'
        }
    ]
    
    for q in questions:
        existing = Quiz.query.filter_by(question=q['question']).first()
        if not existing:
            quiz = Quiz(
                question=q['question'],
                option1=q['option1'],
                option2=q['option2'],
                option3=q['option3'],
                answer=q['answer']
            )
            db.session.add(quiz)
    db.session.commit()
    print("Sample questions added!")

# ========== RUN APP ==========
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_sample_questions()
    app.run(debug=True)