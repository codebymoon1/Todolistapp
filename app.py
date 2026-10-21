from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(200), nullable=False)
  complete = db.Column(db.Boolean, default=False)

  def __repr__(self):
    return f"<Task {self.id}>"


@app.route("/", methods=["POST", "GET"])
def home():
  if request.method == "POST":
    task_title = request.form.get("title")
    if task_title:
      new_task = Task(title=task_title)
      db.session.add(new_task)
      db.session.commit()
    return redirect(url_for("home"))

  # Filter handling
  filter_type = request.args.get("filter", "all")
  if filter_type == "active":
    todo_list = Task.query.filter_by(complete=False).all()
  elif filter_type == "completed":
    todo_list = Task.query.filter_by(complete=True).all()
  else:
    todo_list = Task.query.all()

  # Statistics counters
  total_tasks = Task.query.count()
  completed_tasks = Task.query.filter_by(complete=True).count()
  pending_tasks = total_tasks - completed_tasks

  return render_template(
      "index.html",
      tasks=todo_list,
      current_filter=filter_type,
      total=total_tasks,
      completed=completed_tasks,
      pending=pending_tasks,
  )


@app.route("/update/<int:task_id>")
def update(task_id):
  task = Task.query.get_or_404(task_id)
  task.complete = not task.complete
  db.session.commit()
  return redirect(url_for("home"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
  task = Task.query.get_or_404(task_id)
  db.session.delete(task)
  db.session.commit()
  return redirect(url_for("home"))


@app.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
  task = Task.query.get_or_404(task_id)
  new_title = request.form.get("title")
  if new_title:
    task.title = new_title
    db.session.commit()
  return redirect(url_for("home"))


if __name__ == "__main__":
  with app.app_context():
    db.create_all()
  app.run(debug=True)