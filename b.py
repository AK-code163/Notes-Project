from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_here') 

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General', nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('index'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_username = request.form.get('username')
        entered_password = request.form.get('password')
        
        user = User.query.filter_by(username=entered_username).first()
        
        if user and check_password_hash(user.password, entered_password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # 1. Handle Creating a New Post
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', 'General')
        
        if title and content:
            new_post = Post(title=title, content=content, category=category, user_id=user.id)
            db.session.add(new_post)
            db.session.commit()
            flash('Note created successfully!', 'success')
            return redirect(url_for('dashboard'))
            
    # 2. Get Search, Category Filter, and Pagination Parameters
    search_query = request.args.get('search', '')
    selected_category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Showing 3 notes per page makes pagination easy to test right away!
    
    # Base query for this specific user's posts
    query = Post.query.filter_by(user_id=user.id)
    
    if search_query:
        query = query.filter(
            (Post.title.ilike(f'%{search_query}%')) | (Post.content.ilike(f'%{search_query}%'))
        )
        
    if selected_category:
        query = query.filter(Post.category == selected_category)
        
    # Paginate the filtered query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    
    # Fetch all unique categories this user has used for the filter dropdown
    user_categories = db.session.query(Post.category).filter_by(user_id=user.id).distinct().all()
    categories = [c[0] for c in user_categories]

    return render_template(
        'dashboard.html', 
        user=user, 
        posts=posts, 
        pagination=pagination,
        search_query=search_query,
        categories=categories,
        selected_category=selected_category
    )

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    post = Post.query.get_or_404(post_id)
    if post.user_id != session['user_id']:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    post = Post.query.get_or_404(post_id)
    if post.user_id != session['user_id']:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard'))
        
    db.session.delete(post)
    db.session.commit()
    flash('Note deleted successfully.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/api/notes')
def get_notes_api():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = User.query.get(session['user_id'])
    
    # Convert user posts into a list of dictionaries
    notes_list = []
    for post in user.posts:
        notes_list.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'category': post.category
        })
        
    return jsonify(notes_list)

if __name__ == '__main__':
    app.run(debug=True)