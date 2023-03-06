from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mongoengine import MongoEngine
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import math

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host':'mongodb://localhost/todo_database'
}
login_manager = LoginManager(app)
login_manager.init_app(app)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

app.config['SECRET_KEY'] = 'helloflashtodoapp'
db = MongoEngine()
db.init_app(app)


class User(UserMixin, db.Document):
    meta = {'collection': '<---YOUR_COLLECTION_NAME--->'}
    email = db.StringField(max_length=30)
    password = db.StringField()

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

class Task(db.Document):
    name = db.StringField(required=True)
    creation_date = db.DateTimeField(nullable=False)
    completed =  db.BooleanField(default=False, server_default="false", nullable=False)
    notes = db.StringField()

    def save(self, *args, **kwargs):
        if not self.creation_date:
            self.creation_date = datetime.datetime.now()
        self.modified_date = datetime.datetime.now()
        return super(Task, self).save(*args, **kwargs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        if password == cpassword:
            existing_user = User.objects(email=email).first()
            if existing_user is None:
                hashpass = generate_password_hash(password, method='sha256')
                user = User(email=email, password=hashpass).save()
                login_user(user)
                return redirect(url_for('homepage'))
        else:
            render_template('register.html')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('homepage'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        check_user = User.objects(email=email).first()
        if check_user:
            if check_password_hash(check_user['password'], password):
                login_user(check_user)
                return redirect(url_for('homepage'))
    return render_template('login.html')


@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/")
def homepage():
    """ returns rendered homepage """
    tasks = Task.objects.all()
    last = math.ceil(len(tasks)/int(10))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    tasks = tasks[(page-1)*int(10):(page-1)*int(10)+ int(10)]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template("homepage.html", tasks=tasks, prev=prev, next=next)


@app.route("/create", methods=['POST', 'GET'])
@login_required
def create():
    if request.method=='POST':
        name = request.form.get('name')
        completed = request.form.get('complete')
        notes = request.form.get('notes')
        task = Task(name=name, completed=completed, notes=notes).save()
        return redirect(url_for('homepage'))
    else:
        return render_template('create.html')
    

@app.route("/edit/<task_id>", methods=['POST', 'GET'])
@login_required
def edit(task_id):
    if request.method=='POST':
        name = request.form.get('name')
        notes = request.form.get('notes')
        completed = request.form.get('complete')
        if completed:
            completed=True
        task = Task.objects.get(id=task_id)
        task.update(name=name, completed=completed, notes=notes)
        return redirect(url_for('homepage'))
    else:
        task = Task.objects.get_or_404(id=task_id)
        return render_template('edit.html', task=task)


@app.route("/delete/<task_id>", methods=['POST'])
@login_required
def delete(task_id):

    try:
        task = Task.objects.get_or_404(id=task_id)
        task.delete()
        result = {'success': True, 'response': 'Removed task'}
    except:
        result = {'success': False, 'response': 'Something went wrong'}

    return jsonify(result)