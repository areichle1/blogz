from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:andreareichle@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'andreareichle'
#password is 'andreareichle'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(120))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime)

    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'blog', 'index', 'signup']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/')
def index():
    owner = User.query.all()
    return render_template('index.html', owner=owner)

@app.route('/login', methods=['POST', 'GET'])
def login():
    username_error = ''
    password_error = ''
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        #logs in and redirects to make a blog post page
        if user and user.password == password:
            session['username'] = username
            return redirect ('/newpost')

        if not user:
            username_error = 'Username does not exist.'
            return render_template('login.html', username_error=username_error)

        else:
            password_error = 'Incorrect password, please try again.'
            return render_template('login.html', password_error=password_error)

    return render_template('login.html')

#signup page to create account
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        existing_user = User.query.filter_by(username=username).first()

        username_error = ''
        password_error = ''
        verify_error = ''
        
        #verify username
        if username == '':
            username_error = 'Please enter a username'

        elif len(username) < 3:
            username_error = 'Your username must be between 3 and 20 characters'

        elif existing_user:
            username_error = 'There is already a user with that username'
        
        #verify password
        if password == '':
            password_error = 'Please enter a password'

        elif len(password) < 5:
            password_error = 'Your password must be between 3 and 20 characters'

        #verify the verify password field
        if verify == '':
            verify_error = 'Please enter your password again in this field'

        elif password != verify:
            verify_error = 'Your passwords do not match'

        #adds new user to database
        if not existing_user and len(password) > 3 and password == verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            return render_template('/signup.html', 
            username=username, 
            username_error=username_error, 
            password_error=password_error, 
            verify_error=verify_error)

    return render_template('signup.html')

#displays all blog entries
@app.route('/blog', methods=['GET'])
def blog():

    blog_id = request.args.get('id')
    user_id = request.args.get('user')
    posts = Blog.query.order_by(Blog.pub_date.desc())

    #redirects to a single blog entry page when the blog title is clicked
    if blog_id:
        post = Blog.query.filter_by(id=blog_id).first()
        return render_template("entry.html", post=post)
    #redirects to a page showing entries for single user when username is clicked
    if user_id:
        entries = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('singleUser.html', entries=entries)

    return render_template('blog.html', posts=posts)

#directs to a page of all of the blog posts of a single user
@app.route('/user', methods=['GET'])
def user():
    blog_id = request.args.get('id')
    user_id = request.args.get('user')
    entries = Blog.query.filter_by(owner_id=user_id).all()
    author_id = entries.author_id
    user = User.query.get(author_id)
    return render_template('singleUser.html', user_id=blog_id, blog=entries, user=author_id, username=user)

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    if request.method == 'POST':
        blog_title = request.form['blog-title']
        blog_body = request.form['blog-body']
        owner = User.query.filter_by(username=session['username']).first()
        title_error = ''
        body_error = ''

        #check if input spots are empty
        if not blog_title:
            title_error = 'Please fill in the title'
        if not blog_body:
            body_error = 'Please fill in the body'

        #adds entry to database, displays new entry page
        if not body_error and not title_error:
            new_entry = Blog(blog_title, blog_body, owner)     
            db.session.add(new_entry)
            db.session.commit()        
            return redirect('/blog?id={}'.format(new_entry.id)) 
        else:
            return render_template('newpost.html', title_error=title_error, body_error=body_error, 
                blog_title=blog_title, blog_body=blog_body)
    
    return render_template('newpost.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

if __name__ == '__main__':
    app.run()