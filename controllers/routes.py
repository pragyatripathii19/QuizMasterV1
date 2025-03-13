from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, User, Subject, Chapter, Quiz, Question, Score

from datetime import datetime, timedelta, time
from app import app
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
import io  
import base64  
from sqlalchemy import or_
from functools import wraps


# Helper function to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first!")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# HOME/INDEX PAGE
@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found. Please log in again.")
        session.clear()
        return redirect(url_for('login'))

    if user.is_admin:
        return redirect(url_for('admin'))
    return render_template('index.html')  

@app.route('/admin/search')
@login_required
def admin_search():
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash("You are not authorized to view this page!")
        return redirect(url_for('index'))

    query = request.args.get('query', '')
    filter_type = request.args.get('filter', 'users')

    if filter_type == 'users':
        search_results = User.query.filter(
            or_(User.username.ilike(f'%{query}%'),
                User.full_name.ilike(f'%{query}%')),
            User.is_admin == False  # Exclude admin users
        ).all()
    elif filter_type == 'subjects':
        search_results = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    elif filter_type == 'quizzes':
        search_results = Quiz.query.filter(Quiz.title.ilike(f'%{query}%')).all()
    else:
        search_results = []

    return render_template('admin_dashboard.html',
                           search_results=search_results,
                           filter=filter_type,
                           subjects=Subject.query.all(),
                           query=query)  

@app.route('/admin/user/<int:user_id>')
@login_required
def show_user(user_id):
    user = User.query.get_or_404(user_id)

    # Calculate average scores per subject
    subject_scores = {}
    for score in Score.query.filter_by(user_id=user_id).all():
        quiz = score.quiz
        chapter = quiz.chapter
        subject = chapter.subject
        if subject.name not in subject_scores:
            subject_scores[subject.name] = []
        subject_scores[subject.name].append(score.total_scored)
    
    average_scores = {}
    for subject, scores in subject_scores.items():
        if scores:  # Ensure there are scores to average
            average_scores[subject] = sum(scores) / len(scores)
        else:
            average_scores[subject] = 0  # Or some other default value

    # Generate the chart
    if average_scores:
        plt.figure(figsize=(10, 6))
        plt.bar(average_scores.keys(), average_scores.values())
        plt.xlabel('Subject')
        plt.ylabel('Average Score')
        plt.title('Average Scores per Subject')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        chart_image = base64.b64encode(img.read()).decode()
    else:
        chart_image = None

    return render_template('search_user.html', 
                           user=user,
                           chart_image=chart_image)

@app.route('/admin/subject/<int:subject_id>')
@login_required
def show_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    num_chapters = Chapter.query.filter_by(subject_id=subject_id).count()
    num_quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subject_id).count()

    # Get all scores for quizzes related to this subject
    scores = Score.query.join(Quiz).join(Chapter).filter(Chapter.subject_id == subject_id).all()

    # Calculate highest and lowest scores
    if scores:
        highest_score = max(scores, key=lambda score: score.total_scored)
        lowest_score = min(scores, key=lambda score: score.total_scored)

        highest_score_value = highest_score.total_scored
        lowest_score_value = lowest_score.total_scored

        # Generate the chart
        plt.figure(figsize=(8, 6))
        plt.bar(['Highest Score', 'Lowest Score'], [highest_score_value, lowest_score_value], color=['green', 'red'])
        plt.ylabel('Score')
        plt.title('Highest and Lowest Scores in Subject')
        plt.xticks(['Highest Score', 'Lowest Score'])
        plt.tight_layout()

        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        chart_image = base64.b64encode(img.read()).decode()
    else:
        highest_score_value = None
        lowest_score_value = None
        chart_image = None

    return render_template('search_subject.html',
                           subject=subject,
                           num_chapters=num_chapters,
                           num_quizzes=num_quizzes,
                           chart_image=chart_image,
                           highest_score_value=highest_score_value,
                           lowest_score_value=lowest_score_value)

@app.route('/admin/quiz/<int:quiz_id>')
@login_required
def show_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    num_questions = Question.query.filter_by(quiz_id=quiz_id).count()

    # Get all scores for this quiz
    scores = Score.query.filter_by(quiz_id=quiz_id).all()

    # Calculate highest and lowest scores
    if scores:
        highest_score = max(scores, key=lambda score: score.total_scored).total_scored
        lowest_score = min(scores, key=lambda score: score.total_scored).total_scored
        # Generate the chart
        plt.figure(figsize=(6, 4))
        plt.bar(['Highest Score', 'Lowest Score'], [highest_score, lowest_score], color=['green', 'red'])
        plt.ylabel('Score')
        plt.title('Highest and Lowest Scores in Quiz')
        plt.xticks(['Highest Score', 'Lowest Score'])
        plt.tight_layout()

        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        chart_image = base64.b64encode(img.read()).decode()
    else:
        highest_score = None
        lowest_score = None
        chart_image = None

    return render_template('search_quizzes.html',
                           quiz=quiz,
                           num_questions=num_questions,
                           chart_image=chart_image,
                           highest_score=highest_score,
                           lowest_score=lowest_score)

@app.route('/admin/summary')
@login_required
def admin_summary():
    # Subject-wise Top Score Chart
    subjects = Subject.query.all()
    top_scores = {}
    for subject in subjects:
        # Find the quiz with the highest score in the subject
        highest_score = Score.query.join(Quiz).join(Chapter).filter(Chapter.subject_id == subject.id).order_by(Score.total_scored.desc()).first()
        if highest_score:
            total_questions = len(highest_score.quiz.questions)
            if total_questions > 0:
                top_scores[subject.name] = (highest_score.total_scored / total_questions) * 100
            else:
                top_scores[subject.name] = 0
        else:
            top_scores[subject.name] = 0  # No scores available

    plt.figure(figsize=(10, 6))
    subject_names = list(top_scores.keys())
    subject_scores = list(top_scores.values())
    plt.bar(subject_names, subject_scores, color='skyblue')
    plt.xlabel('Subject')
    plt.ylabel('Top Score (%)')
    plt.title('Subject-wise Top Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    top_score_chart = base64.b64encode(img.read()).decode()

    # Average Score in Each Subject Chart
    average_scores = {}
    for subject in subjects:
        scores = Score.query.join(Quiz).join(Chapter).filter(Chapter.subject_id == subject.id).all()
        if scores:
            average_scores[subject.name] = sum(score.total_scored for score in scores) / len(scores)
        else:
            average_scores[subject.name] = 0

    plt.figure(figsize=(10, 6))
    subject_names = list(average_scores.keys())
    subject_avg_scores = list(average_scores.values())
    plt.bar(subject_names, subject_avg_scores, color='lightgreen')
    plt.xlabel('Subject')
    plt.ylabel('Average Score')
    plt.title('Average Score in Each Subject')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    average_score_chart = base64.b64encode(img.read()).decode()

    # Percentage of Users Who Attempted Quizzes of Each Subject Chart
    subject_user_counts = {}
    total_users = User.query.count()
    for subject in subjects:
        # Count the number of unique users who have attempted quizzes in the subject
        #user_count = Score.query.join(Quiz).join(Chapter).filter(Chapter.subject_id == subject.id).distinct(Score.user_id).count()
        user_count = db.session.query(Score.user_id).join(Quiz).join(Chapter) \
                .filter(Chapter.subject_id == subject.id) \
                .distinct().count()

        subject_user_counts[subject.name] = (user_count / total_users) * 100 if total_users > 0 else 0

    plt.figure(figsize=(8, 6))
    subject_names = list(subject_user_counts.keys())
    user_percentages = list(subject_user_counts.values())
    plt.pie(user_percentages, labels=subject_names, autopct='%1.1f%%', startangle=140)
    plt.title('Percentage of Users Who Attempted Quizzes of Each Subject')
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    users_attempted_chart = base64.b64encode(img.read()).decode()

    return render_template('admin_summary.html', 
                           top_score_chart=top_score_chart,
                           average_score_chart=average_score_chart,
                           users_attempted_chart=users_attempted_chart)

# ADMIN DASHBOARD
@app.route('/admin')
@login_required
def admin():
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found. Please log in again.")
        session.clear()
        return redirect(url_for('login'))
    
    if not user.is_admin:
        flash("You are not authorized to view this page!")
        return render_template('index.html')
    
    # Fetch all subjects from the database
    subjects = Subject.query.all()
    return render_template('admin_dashboard.html', subjects=subjects)

# LOGIN GET AND POST ROUTES
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    
    if username == '' or password == '':
        flash('Username or password cannot be empty!')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User does not exist')
        return redirect(url_for('login'))
    if not user.verify_password(password):
        flash('Incorrect password')
        return redirect(url_for('login'))

    flash('Login successful!')
    session['user_id'] = user.id

    # Redirect admin to admin dashboard, users to user dashboard
    if user.is_admin:
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('user_dashboard'))
    
    
#REGISTER LOGIN/POST ROUTES
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form['username']
    password = request.form['password']
    full_name = request.form['full_name']
    qualification = request.form['qualification']
    dob = request.form['dob']

    if username=='' or password=='':
        flash('Username or password cannot be empty!')
        return redirect(url_for('register'))
        
    if User.query.filter_by(username=username).first():
        flash("User with this username already exists! ")
        return redirect(url_for('register'))

    try:
        # Convert dob string to datetime object (assuming YYYY-MM-DD format)
        dob = datetime.strptime(dob, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Please use 'YYYY-MM-DD'.")
        return redirect(url_for('register'))

    new_user = User(username=username, password=password, full_name=full_name,
                        qualification=qualification, dob=dob)
    db.session.add(new_user)
    db.session.commit()

    flash("Registration successful!", category='success')
    return redirect(url_for('login'))


#ALL SUBJECT RELATED ROUTES
@app.route('/add_subject')
def add_subject():
    return render_template('add_subject.html')

@app.route('/add_subject', methods=['POST'])
def add_subject_post():
    subject_name = request.form['name']
    subject_description = request.form['description']
    
    # Validate subject name
    if not subject_name or len(subject_name) > 120:
        flash('Subject name cannot be empty and must be less than or equal to 120 characters.', 'error')
        return redirect(url_for('add_subject'))
    
    # Create and add new subject to the database
    new_subject = Subject(name=subject_name, description=subject_description)
    db.session.add(new_subject)
    db.session.commit()
    
    flash('Subject added successfully!', 'success')
    return redirect(url_for('admin'))  

@app.route('/edit_subject/<int:id>', methods=['GET', 'POST'])
def edit_subject(id):
    # Fetch the subject by id
    subject = Subject.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get the updated values from the form
        subject.name = request.form['name']
        subject.description = request.form['description']
        
        # Validate the subject name
        if not subject.name or len(subject.name) > 120:
            flash('Subject name cannot be empty and must be less than or equal to 120 characters.', 'error')
            return redirect(url_for('edit_subject', id=id))

        # Commit the changes to the database
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin'))  # Redirect back to the admin dashboard

    # Render the form with the current subject data pre-filled
    return render_template('edit_subject.html', subject=subject)


@app.route('/delete_subject/<int:id>', methods=['GET', 'POST'])
def delete_subject(id):
    # Fetch the subject by id
    subject = Subject.query.get_or_404(id)
    
    # Delete the subject from the database
    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('admin'))  


@app.route('/show_chapters/<int:subject_id>', methods=['GET'])
def show_chapters(subject_id):
    # Fetch the subject by id
    subject = Subject.query.get_or_404(subject_id)

    # Fetch the chapters related to this subject 
    chapters = Chapter.query.filter_by(subject_id=subject.id).all()

    return render_template('chapters.html', subject=subject, chapters=chapters)


#ROUTES FOR CHAPTERS WITHIN SUBJECTS

@app.route('/add_chapter/<int:subject_id>', methods=['GET', 'POST'])
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        chapter_name = request.form['name']
        chapter_description = request.form['description']

        if not chapter_name:
            flash('Chapter name cannot be empty.', 'error')
            return redirect(url_for('add_chapter', subject_id=subject_id))

        new_chapter = Chapter(name=chapter_name, description=chapter_description, subject_id=subject.id)
        db.session.add(new_chapter)
        db.session.commit()

        flash('Chapter added successfully!', 'success')
        return redirect(url_for('show_chapters', subject_id=subject_id))

    return render_template('add_chapter.html', subject=subject)


@app.route('/edit_chapter/<int:id>', methods=['GET', 'POST'])
def edit_chapter(id):
    # Fetch the chapter by id
    chapter = Chapter.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get the updated values from the form
        chapter.name = request.form['name']
        chapter.description = request.form['description']
        
        # Validate the chapter name
        if not chapter.name or len(chapter.name) > 120:
            flash('Chapter name cannot be empty and must be less than or equal to 120 characters.', 'error')
            return redirect(url_for('edit_chapter', id=id))

        # Commit the changes to the database
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('show_chapters', subject_id=chapter.subject_id))

    # Render the form with the current chapter data pre-filled
    return render_template('edit_chapter.html', chapter=chapter)



@app.route('/delete_chapter/<int:id>', methods=['GET', 'POST'])
def delete_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    subject_id = chapter.subject_id  # Get the subject_id of the chapter
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash('Chapter deleted successfully!', 'success')
    
    # Redirect to the updated show_chapters page
    return redirect(url_for('show_chapters', subject_id=subject_id))



@app.route('/show_quizzes/<int:id>', methods=['GET'])
def show_quizzes(id):
    # Fetch the chapter by id
    chapter = Chapter.query.get_or_404(id)

    # Fetch quizzes related to this chapter
    quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()

    return render_template('quizzes.html', chapter=chapter, quizzes=quizzes)

#ROUTES FOR QUIZZES INSIDE EACH CHAPTER

@app.route('/add_quiz/<int:chapter_id>', methods=['GET', 'POST'])
def add_quiz(chapter_id):
    # Fetch the chapter for which the quiz is being added
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        # Fetch form data
        title = request.form.get('title')
        date_of_quiz = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')

        # Validate and convert time_duration to `datetime.time` format (HH:MM)
        try:
            hours, minutes = map(int, time_duration.split(':'))
            time_duration_obj =time(hours, minutes,0)  
        except ValueError:
            flash("Invalid time duration format. Use HH:MM.", "danger")
            return render_template('add_quiz.html', chapter=chapter)

        # Convert the date string to a `datetime.date` object
        try:
            date_of_quiz_obj = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return render_template('add_quiz.html', chapter=chapter)

        # Create a new quiz object
        new_quiz = Quiz(
            chapter_id=chapter_id,
            title=title,  # Add the title from the form
            date_of_quiz=date_of_quiz_obj,
            time_duration=time_duration_obj,
            remarks=remarks
        )

        # Add the quiz to the database
        db.session.add(new_quiz)
        db.session.commit()

        # Flash success message and redirect to the quizzes page for the chapter
        flash('Quiz added successfully!', 'success')
        return redirect(url_for('show_quizzes', id=chapter_id))
    
    # Render the quiz creation form
    return render_template('add_quiz.html', chapter=chapter)

@app.route('/edit_quiz/<int:id>', methods=['GET', 'POST'])
def edit_quiz(id):
    # Fetch the quiz to edit
    quiz = Quiz.query.get_or_404(id)

    if request.method == 'POST':
        # Fetch form data
        title = request.form.get('title')
        date_of_quiz = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')

        # Validate and convert time_duration to datetime.time format (HH:MM)
        try:
            hours, minutes = map(int, time_duration.split(':'))
            time_duration_obj = time(hours, minutes, 0)
        except ValueError:
            flash("Invalid time duration format. Use HH:MM.", "danger")
            return render_template('edit_quiz.html', quiz=quiz)

        # Convert the date string to a datetime.date object
        try:
            date_of_quiz_obj = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return render_template('edit_quiz.html', quiz=quiz)

        # Update the quiz object with new data
        quiz.title = title
        quiz.date_of_quiz = date_of_quiz_obj
        quiz.time_duration = time_duration_obj
        quiz.remarks = remarks

        # Save changes to the database
        db.session.commit()

        # Flash success message and redirect to the quizzes page for the chapter
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('show_quizzes', id=quiz.chapter_id))

    # Render the quiz edit form with existing data
    return render_template('edit_quiz.html', quiz=quiz)


@app.route('/delete_quiz/<int:id>', methods=['GET', 'POST'])
def delete_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    chapter_id = quiz.chapter_id  # Get the chapter_id of the quiz

    db.session.delete(quiz)
    db.session.commit()

    flash('Quiz deleted successfully!', 'success')

    # Redirect to the updated quiz management page
    return redirect(url_for('show_quizzes', id=chapter_id))


# Show questions for a quiz
@app.route('/quiz/<int:quiz_id>/questions')
def show_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('questions.html', quiz_id=quiz.id, quiz_title=quiz.title, questions=questions)

# Add a new question
@app.route('/quiz/<int:quiz_id>/add_question', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']
        
        new_question = Question(
            quiz_id=quiz.id,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=correct_option
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        return redirect(url_for('show_questions', quiz_id=quiz.id))
    
    return render_template('add_questions.html', quiz_id=quiz.id, quiz_title=quiz.title)

@app.route('/edit_question/<int:id>', methods=['GET', 'POST'])
def edit_question(id):
    # Fetch the question by ID
    question = Question.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update question fields with form data
        question.question_statement = request.form['question_statement']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_answer = request.form['correct_answer']
        
        # Save changes to the database
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('show_questions', quiz_id=question.quiz_id))
    
    # Render an edit form with the existing question details
    return render_template('edit_question.html', question=question)



@app.route('/delete_question/<int:id>', methods=['POST'])
def delete_question(id):
    # Fetch the question by ID
    question = Question.query.get_or_404(id)
    
    # Store quiz_id to redirect back to the quiz's questions page
    quiz_id = question.quiz_id
    
    # Delete the question
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('show_questions', quiz_id=quiz_id))

#USER DASHBOARD ############
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    # Fetch all quizzes
    quizzes = Quiz.query.all()
    
    # Prepare quizzes with additional data (e.g., question count)
    quiz_data = []
    for quiz in quizzes:
        quiz_data.append({
            "id": quiz.id,
            "title": quiz.title,
            "num_questions": len(quiz.questions),
            "date": quiz.date_of_quiz,
            "duration": quiz.time_duration,
        })
    
    return render_template('user_dashboard.html', quizzes=quiz_data)

@app.route('/quiz/<int:quiz_id>/view')
@login_required
def view_quiz(quiz_id):
    #return "view quizz soon"
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('view_quiz.html', quiz=quiz)

@app.route('/start_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions  # This is already a list of all questions

    # Initialize quiz data in session if it's a new attempt
    if 'quiz_data' not in session or session['quiz_data'].get('quiz_id') != quiz_id:
        session['quiz_data'] = {
            'quiz_id': quiz_id,
            'current_question_index': 0,
            'total_marks': 0,
            'answers': {},
            'total_questions': len(questions),
            'questions_attempted': 0
        }
    
    quiz_data = session['quiz_data']
    current_question_index = int(quiz_data['current_question_index'])
    total_questions = int(quiz_data['total_questions'])

    if current_question_index >= total_questions:
        # Quiz finished - redirect to scores
        return redirect(url_for('save_score', quiz_id=quiz_id)) #redirecting to save_score

    question = questions[current_question_index]
    options = [
        {'id': 1, 'text': question.option1},
        {'id': 2, 'text': question.option2},
        {'id': 3, 'text': question.option3},
        {'id': 4, 'text': question.option4},
    ]

    selected_option = None

    if request.method == 'POST':
        selected_option_id = request.form.get('selected_option')
        action = request.form.get('action')

        if selected_option_id:
            selected_option_id = int(selected_option_id)
            quiz_data['questions_attempted'] = int(quiz_data['questions_attempted']) + 1

            # Store the answer in the session
            quiz_data['answers'][str(question.id)] = selected_option_id

            # Check if the answer is correct
            correct_option_text = question.correct_answer
            selected_option_text = next((option['text'] for option in options if option['id'] == selected_option_id), None)

            if selected_option_text == correct_option_text:
                quiz_data['total_marks'] = int(quiz_data['total_marks']) + 1

        if action == 'save_next':
            quiz_data['current_question_index'] = int(quiz_data['current_question_index']) + 1
            session['quiz_data'] = quiz_data  # Update session
            return redirect(url_for('start_quiz', quiz_id=quiz_id))
        elif action == 'submit':
            session['quiz_data'] = quiz_data  # Ensure data is updated
            return redirect(url_for('save_score', quiz_id=quiz_id)) #redirection to save_score

    # If it's a GET request or no option was selected in POST, display the question
    # Check if there's a previously selected option for this question
    if str(question.id) in quiz_data['answers']:
        selected_option = quiz_data['answers'][str(question.id)]

    # Ensure all values in quiz_data are of consistent types
    quiz_data['current_question_index'] = int(quiz_data['current_question_index'])
    quiz_data['total_marks'] = int(quiz_data['total_marks'])
    quiz_data['total_questions'] = int(quiz_data['total_questions'])
    quiz_data['questions_attempted'] = int(quiz_data['questions_attempted'])

    session['quiz_data'] = quiz_data  # Update session with consistent data types

    # Debug: Print session data
    print("Session quiz_data:", session['quiz_data'])

    return render_template(
        'start_quiz.html',
        quiz=quiz,
        question=question,
        options=options,
        current_question_index=current_question_index,  # Corrected: Use current_question_index directly
        total_questions=total_questions,
        selected_option=selected_option
    )

@app.route('/save_score/<int:quiz_id>') #saving score
@login_required
def save_score(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)  # Retrieve the quiz from the database
    quiz_data = session.get('quiz_data')

    if quiz_data and quiz_data.get('quiz_id') == quiz_id:
        total_questions = quiz_data['total_questions']
        total_marks = quiz_data['total_marks']

        # Create a new Score record in the database
        score = Score(
            quiz_id=quiz_id,
            user_id=session['user_id'],
            time_stamp_of_attempt=datetime.now(),
            total_scored=total_marks
        )
        db.session.add(score)
        db.session.commit()

        session.pop('quiz_data', None)  # Clear quiz data after saving score
    return redirect(url_for('scoreboard')) #redirecting to scoreboard

@app.route('/scoreboard')
@login_required
def scoreboard():
    user_id = session['user_id']
    scores = Score.query.filter_by(user_id=user_id).order_by(Score.time_stamp_of_attempt.desc()).all()
    return render_template('scores.html', scores=scores)

def generate_score_trend_chart(user_id):
    """Generates a score trend line chart using Matplotlib."""
    scores = Score.query.filter_by(user_id=user_id).order_by(Score.time_stamp_of_attempt).all()
    if not scores:
        return None  # No data to plot

    dates = [score.time_stamp_of_attempt for score in scores]
    marks = [score.total_scored for score in scores]

    plt.figure(figsize=(8, 4))  
    plt.plot(dates, marks, marker='o', linestyle='-')
    plt.xlabel('Date')
    plt.ylabel('Score')
    plt.title('Score Trend Over Time')
    plt.grid(True)
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.tight_layout()  # Adjust layout to prevent labels from overlapping

    # Save to a BytesIO object and encode to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()  # Close the plot to free memory
    return base64.b64encode(img.read()).decode()

def generate_average_score_bar_chart(user_id):
    """Generates an average score bar chart using Matplotlib."""
    # Fetch all scores for the user
    scores = Score.query.filter_by(user_id=user_id).all()

    if not scores:
        return None  # No data to plot

    # Group scores by quiz ID
    quiz_scores = {}
    for score in scores:
        if score.quiz_id not in quiz_scores:
            quiz_scores[score.quiz_id] = []
        quiz_scores[score.quiz_id].append(score.total_scored)

    # Calculate average score for each quiz
    quiz_averages = {quiz_id: sum(scores) / len(scores) for quiz_id, scores in quiz_scores.items()}

    # Get quiz titles for labels
    quiz_titles = {quiz_id: Quiz.query.get(quiz_id).title for quiz_id in quiz_averages}

    # Prepare data for plotting
    quiz_ids = list(quiz_averages.keys())
    averages = list(quiz_averages.values())
    labels = [quiz_titles[quiz_id] for quiz_id in quiz_ids]

    # Create the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(labels, averages, color='skyblue')
    plt.xlabel('Quiz')
    plt.ylabel('Average Score')
    plt.title('Average Score per Quiz')
    plt.xticks(rotation=45, ha='right')  # Rotate labels for readability
    plt.tight_layout()

    # Convert plot to PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.read()).decode()

def generate_quizzes_attempted_chart(user_id):
    """Generates a quizzes attempted bar chart using Matplotlib."""
    # Fetch all scores for the user
    scores = Score.query.filter_by(user_id=user_id).all()

    if not scores:
        return None  # No data to plot

    # Group scores by week/month
    weekly_attempts = {}
    for score in scores:
        week = score.time_stamp_of_attempt.strftime('%Y-%W')  # Year-Week format
        if week not in weekly_attempts:
            weekly_attempts[week] = 0
        weekly_attempts[week] += 1

    # Prepare data for plotting
    weeks = list(weekly_attempts.keys())
    attempts = list(weekly_attempts.values())

    # Create the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(weeks, attempts, color='lightgreen')
    plt.xlabel('Week (Year-Week)')
    plt.ylabel('Number of Quizzes Attempted')
    plt.title('Quizzes Attempted per Week')
    plt.xticks(rotation=45, ha='right')  # Rotate labels for readability
    plt.tight_layout()

    # Convert plot to PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.read()).decode()

@app.route('/user_summary')
@login_required
def user_summary():
    user_id = session['user_id']

    # Generate charts
    score_trend_chart = generate_score_trend_chart(user_id)
    average_score_chart = generate_average_score_bar_chart(user_id)
    quizzes_attempted_chart = generate_quizzes_attempted_chart(user_id)

    return render_template(
        'user_summary.html',
        score_trend_chart=score_trend_chart,
        average_score_chart=average_score_chart,
        quizzes_attempted_chart=quizzes_attempted_chart
    )

