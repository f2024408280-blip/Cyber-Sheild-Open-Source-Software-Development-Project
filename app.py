from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import re
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'CyberShieldSecretKey2024'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)

class UserQuizProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    attempted_question_ids = db.Column(db.String(1000), default='')
    total_score = db.Column(db.Integer, default=0)

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)

# ==================== HELPER FUNCTIONS ====================

def get_user_progress(username):
    progress = UserQuizProgress.query.filter_by(username=username).first()
    if not progress:
        progress = UserQuizProgress(username=username, attempted_question_ids='', total_score=0)
        db.session.add(progress)
        db.session.commit()
    return progress

def update_user_progress(username, question_id, is_correct):
    progress = get_user_progress(username)
    
    attempted_list = [int(x) for x in progress.attempted_question_ids.split(',') if x]
    if question_id not in attempted_list:
        if progress.attempted_question_ids:
            progress.attempted_question_ids += f',{question_id}'
        else:
            progress.attempted_question_ids = str(question_id)
        
        if is_correct:
            progress.total_score += 10
        
        db.session.commit()
    
    return progress.total_score

def reset_user_progress(username):
    progress = get_user_progress(username)
    progress.attempted_question_ids = ''
    db.session.commit()

def update_leaderboard(username, score):
    entry = Leaderboard.query.filter_by(username=username).first()
    if entry:
        entry.score = score
    else:
        entry = Leaderboard(username=username, score=score)
        db.session.add(entry)
    db.session.commit()

def get_next_question(username):
    progress = get_user_progress(username)
    all_questions = QuizQuestion.query.all()
    
    if not all_questions:
        return None
    
    attempted_ids = [int(x) for x in progress.attempted_question_ids.split(',') if x]
    available_questions = [q for q in all_questions if q.id not in attempted_ids]
    
    if not available_questions:
        reset_user_progress(username)
        available_questions = all_questions
    
    return random.choice(available_questions)

# ==================== ROUTES ====================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    
    progress = get_user_progress(session['username'])
    total_questions = QuizQuestion.query.count()
    attempted_count = len([x for x in progress.attempted_question_ids.split(',') if x])
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         score=progress.total_score,
                         attempted=attempted_count,
                         total=total_questions)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template('register.html', error='Username already exists')
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Demo account
        if username == 'demo' and password == 'demo123':
            session['username'] = username
            return redirect('/dashboard')
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# ==================== QUIZ SYSTEM ====================

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    
    if request.method == 'POST':
        question_id = int(request.form['question_id'])
        selected_answer = request.form['answer']
        correct_answer = request.form['correct_answer']
        
        is_correct = (selected_answer == correct_answer)
        
        new_score = update_user_progress(username, question_id, is_correct)
        update_leaderboard(username, new_score)
        
        next_question = get_next_question(username)
        
        if is_correct:
            result = 'CORRECT! +10 points'
            result_type = 'correct'
        else:
            result = 'INCORRECT! The correct answer is: ' + correct_answer
            result_type = 'incorrect'
        
        progress = get_user_progress(username)
        attempted_count = len([x for x in progress.attempted_question_ids.split(',') if x])
        total_questions = QuizQuestion.query.count()
        
        if total_questions > 0:
            progress_percent = int((attempted_count / total_questions) * 100)
        else:
            progress_percent = 0
        
        return render_template('quiz.html', 
                             question=next_question,
                             result=result,
                             result_type=result_type,
                             score=progress.total_score,
                             attempted=attempted_count,
                             total=total_questions,
                             progress_percent=progress_percent)
    
    question = get_next_question(username)
    progress = get_user_progress(username)
    attempted_count = len([x for x in progress.attempted_question_ids.split(',') if x])
    total_questions = QuizQuestion.query.count()
    
    if total_questions > 0:
        progress_percent = int((attempted_count / total_questions) * 100)
    else:
        progress_percent = 0
    
    return render_template('quiz.html',
                         question=question,
                         result=None,
                         result_type=None,
                         score=progress.total_score,
                         attempted=attempted_count,
                         total=total_questions,
                         progress_percent=progress_percent)

# ==================== LEADERBOARD ====================

@app.route('/leaderboard')
def leaderboard():
    top_players = Leaderboard.query.order_by(Leaderboard.score.desc()).limit(10).all()
    return render_template('leaderboard.html', players=top_players)

# ==================== PHISHING DETECTOR ====================

SUSPICIOUS_KEYWORDS = ['secure', 'verify', 'login', 'update', 'confirm', 'banking', 'paypal', 'amazon', 'google', 'microsoft', 'alert', 'suspicious', 'unusual', 'activity', 'verify now']

@app.route('/phishing', methods=['GET', 'POST'])
def phishing():
    result = None
    if request.method == 'POST':
        url = request.form['url'].lower()
        suspicious_found = [kw for kw in SUSPICIOUS_KEYWORDS if kw in url]
        
        if suspicious_found:
            result = {
                'status': 'danger', 
                'message': 'Phishing detected!', 
                'details': suspicious_found
            }
        elif not url.startswith(('http://', 'https://')):
            result = {
                'status': 'warning', 
                'message': 'Invalid URL format. Please include http:// or https://'
            }
        else:
            result = {
                'status': 'success', 
                'message': 'URL appears to be safe'
            }
    
    return render_template('phishing.html', result=result)

# ==================== BREACH CHECKER ====================

BREACHED_DATABASE = {
    'test@example.com': 'LinkedIn Breach 2021',
    'admin@company.com': 'Adobe Breach 2013',
    'user@gmail.com': 'Dropbox Breach 2012',
    'john@yahoo.com': 'Yahoo Breach 2014',
    'demo@test.com': 'Collection 1 Breach 2019'
}

@app.route('/breach', methods=['GET', 'POST'])
def breach():
    result = None
    if request.method == 'POST':
        email = request.form['email'].lower()
        
        if email in BREACHED_DATABASE:
            result = {
                'status': 'danger', 
                'message': 'Email found in data breach!', 
                'breach': BREACHED_DATABASE[email]
            }
        else:
            result = {
                'status': 'success', 
                'message': 'Email not found in known data breaches'
            }
    
    return render_template('breach.html', result=result)

# ==================== PASSWORD ANALYZER WITH DETAILED CRITERIA ====================

COMMON_PASSWORDS = ['password', '123456', 'qwerty', 'admin', 'welcome', 'letmein', 'password123', 'admin123', '12345678', 'abcdef', 'abc123', 'iloveyou', 'monkey', 'dragon', 'master']

@app.route('/password', methods=['GET', 'POST'])
def password():
    analysis = None
    if request.method == 'POST':
        pwd = request.form['password']
        
        # Initialize criteria
        criteria = {
            'length': len(pwd) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', pwd)),
            'lowercase': bool(re.search(r'[a-z]', pwd)),
            'numbers': bool(re.search(r'[0-9]', pwd)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd)),
            'not_common': pwd.lower() not in COMMON_PASSWORDS
        }
        
        # Calculate score
        score = 0
        max_score = 6
        feedback = []
        
        # Length check
        if criteria['length']:
            score += 1
            if len(pwd) >= 12:
                score += 0.5
                max_score += 0.5
                feedback.append('Good length (12+ characters)')
        else:
            feedback.append('Password must be at least 8 characters long')
        
        # Uppercase check
        if criteria['uppercase']:
            score += 1
            feedback.append('Contains uppercase letters')
        else:
            feedback.append('Add uppercase letters (A-Z) for better security')
        
        # Lowercase check
        if criteria['lowercase']:
            score += 1
            feedback.append('Contains lowercase letters')
        else:
            feedback.append('Add lowercase letters (a-z)')
        
        # Numbers check
        if criteria['numbers']:
            score += 1
            feedback.append('Contains numbers')
        else:
            feedback.append('Include numbers (0-9) to strengthen your password')
        
        # Special characters check
        if criteria['special']:
            score += 1
            feedback.append('Contains special characters')
        else:
            feedback.append('Add special characters (!@#$%^&*) for maximum security')
        
        # Common password check
        if not criteria['not_common']:
            score = 0
            feedback = ['This is a commonly used password. Choose a unique, unpredictable password.']
        else:
            score += 1
            feedback.append('Not a commonly used password')
        
        # Calculate percentage
        percentage = (score / max_score) * 100
        percentage = min(100, max(0, percentage))
        
        # Determine strength
        if percentage >= 80:
            strength = 'Very Strong'
            if not feedback:
                feedback = ['Excellent! Your password meets all security standards.']
        elif percentage >= 60:
            strength = 'Strong'
        elif percentage >= 30:
            strength = 'Weak'
        else:
            strength = 'Very Weak'
        
        # Remove duplicate feedback and clean up
        unique_feedback = []
        for item in feedback:
            if item not in unique_feedback:
                unique_feedback.append(item)
        
        analysis = {
            'strength': strength,
            'percentage': percentage,
            'feedback': unique_feedback,
            'criteria': criteria
        }
    
    return render_template('password.html', analysis=analysis)

# ==================== CAESAR CIPHER ====================

def caesar_cipher(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            start = 65 if char.isupper() else 97
            result += chr((ord(char) - start + shift) % 26 + start)
        else:
            result += char
    return result

@app.route('/cipher', methods=['GET', 'POST'])
def cipher():
    result = None
    if request.method == 'POST':
        message = request.form['message']
        shift = int(request.form['shift'])
        action = request.form['action']
        
        if action == 'encrypt':
            result = caesar_cipher(message, shift)
        else:
            result = caesar_cipher(message, -shift)
    
    return render_template('cipher.html', result=result)

# ==================== INITIALIZE DATABASE ====================

def init_quiz_questions():
    questions = [
        ("What is the most common type of cyber attack?", "Phishing", "Ransomware", "DDoS", "Phishing"),
        ("What does HTTPS stand for?", "HyperText Transfer Protocol Secure", "High Transfer Protocol", "Hyper Transfer System", "HyperText Transfer Protocol Secure"),
        ("Which is a strong password?", "password123", "P@ssw0rd!2024", "qwerty123", "P@ssw0rd!2024"),
        ("What is 2FA?", "Two passwords", "Two step verification", "Two devices", "Two step verification"),
        ("What is ransomware?", "Encrypts files for ransom", "Steals passwords", "Spreads via email", "Encrypts files for ransom"),
        ("What is a firewall?", "Network monitor", "Antivirus", "Password manager", "Network monitor"),
        ("What is social engineering?", "Psychological manipulation", "Software hacking", "Network attack", "Psychological manipulation"),
        ("What does VPN stand for?", "Virtual Private Network", "Virtual Public Network", "Verified Private Network", "Virtual Private Network"),
        ("What is a zero-day vulnerability?", "Unknown security flaw", "Old software bug", "Weak password", "Unknown security flaw"),
        ("Best defense against phishing?", "Check email sender", "Use antivirus", "Update Windows", "Check email sender"),
        ("What is SQL Injection?", "Database attack", "Network attack", "Physical attack", "Database attack"),
        ("What does DDoS stand for?", "Distributed Denial of Service", "Direct Denial of Security", "Digital Denial", "Distributed Denial of Service"),
        ("Purpose of encryption?", "Protect data confidentiality", "Speed up transfer", "Compress data", "Protect data confidentiality"),
        ("What is brute force attack?", "Trying all passwords", "Social engineering", "Malware", "Trying all passwords"),
        ("What is multi-factor authentication?", "Multiple verification methods", "Multiple passwords", "Multiple devices", "Multiple verification methods")
    ]
    
    for q in questions:
        existing = QuizQuestion.query.filter_by(question=q[0]).first()
        if not existing:
            new_q = QuizQuestion(
                question=q[0],
                option_a=q[1],
                option_b=q[2],
                option_c=q[3],
                correct_answer=q[4]
            )
            db.session.add(new_q)
    
    db.session.commit()
    print(f"Added {len(questions)} quiz questions")

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_quiz_questions()
    app.run(debug=True, port=5000)