from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret-key-change-this"  # Required for sessions
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User Model
class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(150), unique=True, nullable=False)
  password = db.Column(db.String(150), nullable=False)
  tasks = db.relationship("Task", backref="user", lazy=True)


# Task Model (now linked to a specific user)
class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(200), nullable=False)
  complete = db.Column(db.Boolean, default=False)
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

  def __repr__(self):
    return f"<Task {self.id}>"


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


# Home Route (Protected - only shows current user's tasks)
@app.route("/", methods=["POST", "GET"])
@login_required
def home():
  if request.method == "POST":
    task_title = request.form.get("title")
    if task_title:
      new_task = Task(title=task_title, user_id=current_user.id)
      db.session.add(new_task)
      db.session.commit()
    return redirect(url_for("home"))

  filter_type = request.args.get("filter", "all")
  if filter_type == "active":
    todo_list = Task.query.filter_by(
        user_id=current_user.id, complete=False
    ).all()
  elif filter_type == "completed":
    todo_list = Task.query.filter_by(
        user_id=current_user.id, complete=True
    ).all()
  else:
    todo_list = Task.query.filter_by(user_id=current_user.id).all()

  total_tasks = Task.query.filter_by(user_id=current_user.id).count()
  completed_tasks = Task.query.filter_by(
      user_id=current_user.id, complete=True
  ).count()
  pending_tasks = total_tasks - completed_tasks

  return render_template(
      "index.html",
      tasks=todo_list,
      current_filter=filter_type,
      total=total_tasks,
      completed=completed_tasks,
      pending=pending_tasks,
  )


# Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    user_exists = User.query.filter_by(username=username).first()
    if user_exists:
      flash("Username already exists. Please choose a different one.")
      return redirect(url_for("signup"))

    hashed_password = generate_password_hash(password, method="scrypt")
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    return redirect(url_for("home"))

  return render_template("signup.html")


# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
      login_user(user)
      return redirect(url_for("home"))
    else:
      flash("Invalid username or password.")

  return render_template("login.html")


# Logout Route
@app.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("login"))


# Task Update Route
@app.route("/update/<int:task_id>")
@login_required
def update(task_id):
  task = Task.query.get_or_404(task_id)
  if task.user_id == current_user.id:
    task.complete = not task.complete
    db.session.commit()
  return redirect(url_for("home"))


# Task Delete Route
@app.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
  task = Task.query.get_or_404(task_id)
  if task.user_id == current_user.id:
    db.session.delete(task)
    db.session.commit()
  return redirect(url_for("home"))


# Task Edit Route
@app.route("/edit/<int:task_id>", methods=["POST"])
@login_required
def edit(task_id):
  task = Task.query.get_or_404(task_id)
  if task.user_id == current_user.id:
    new_title = request.form.get("title")
    if new_title:
      task.title = new_title
      db.session.commit()
  return redirect(url_for("home"))


if __name__ == "__main__":
  with app.app_context():
    db.create_all()
  app.run(debug=True)