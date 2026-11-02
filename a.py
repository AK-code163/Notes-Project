from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 1. UPDATED USER MODEL (Added a password column)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # <-- New password column

    def __repr__(self): # Without it print user will user code output(in terminal only, not in webpages)
        return f'<User {self.username}>'


# 2. ROUTE TO ADD A TEST USER WITH A PASSWORD
@app.route('/')
def home():
    # Check if user already exists to prevent unique constraint errors
    existing_user = User.query.filter_by(username="developer_pro").first()
    if existing_user:
        return "Test user already exists!"
        
    new_user = User(
        username="developer_pro", 
        email="dev@example.com", 
        password="secretpassword"  # <-- Setting a test password
    )
    db.session.add(new_user)
    db.session.commit()
    return "User saved successfully! You can now try logging in."


# 3. LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_username = request.form.get('username')
        entered_password = request.form.get('password')
        
        # Search database for the user
        user = User.query.filter_by(username=entered_username).first()
        
        # Check if user exists and password matches
        if user and user.password == entered_password:
            return f"Welcome back, {user.username}! You are successfully logged in."
        else:
            return "Invalid username or password. Please try again.", 401
            
    # Simple built-in HTML form for testing
    return '''
        <form method="POST">
            <h2>Login</h2>
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Log In</button>
        </form>
    '''


if __name__ == '__main__':
    app.run(debug=True)