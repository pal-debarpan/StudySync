from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "study_sync_secret"

@app.route('/')
def home():
    return render_template('index.html', active_page="home")

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE email = ?
            """, (email,))
        user = cursor.fetchone()

        if user is None:
            conn.close()
            flash("Email does not exists.", "error")
            return redirect(url_for("login"))

        if check_password_hash(user[3], password):
            session["logged_in"] = True
            session["email"] = email
            conn.close()
            return redirect("/dashboard")
        else:
            conn.close()
            flash("Incorrect Password.", "error")
            return redirect(url_for("login"))
        

    return render_template("login.html", active_page="login")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()


        try:
            cursor.execute("""
                        INSERT INTO users(fullname, email, password)
                        VALUES(?, ?, ?)""", (fullname, email, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already exists.", "error")
            return redirect(url_for("login"))

        finally:
            conn.close()


        return redirect("/login")



    return render_template("signup.html", active_page="signup")

@app.route('/dashboard')
def dashboard():

    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, fullname
    FROM users
    WHERE email = ?
    """, (session["email"],))

    user = cursor.fetchone()

    user_id = user[0]
    fullname = user[1]

    cursor.execute("""
    SELECT COUNT(*)
    FROM notes
    WHERE user_id = ?
    """, (user_id,))

    notes_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM assignments
    WHERE user_id = ?
    """, (user_id,))

    assignments_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT SUM(pomodoros_completed)
    FROM assignments
    WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()[0]

    total_pomodoros = result if result else 0

    cursor.execute("""
    SELECT COUNT(*)
    FROM assignments
    WHERE user_id = ?
    AND status = 'Completed'
    """, (user_id,))

    completed_assignments = cursor.fetchone()[0]
    pending_assignments = assignments_count - completed_assignments

    if assignments_count == 0:
        completion_rate = 0
    else:
        completion_rate = int((completed_assignments / assignments_count) * 100)

    cursor.execute("""
    SELECT title, due_date
    FROM assignments
    WHERE user_id = ?
    AND status = 'Pending'
    ORDER BY due_date ASC
    LIMIT 5
    """, (user_id,))

    upcoming_assignments = cursor.fetchall()

    formatted_assignments = []

    today = date.today()

    for assignment in upcoming_assignments:

        title = assignment[0]

        due = datetime.strptime(assignment[1], "%Y-%m-%d").date()

        days = (due - today).days

        if days == 0:
            due_text = "📅 Due Today"

        elif days == 1:
            due_text = "📅 Due Tomorrow"

        elif days > 1:
            due_text = f"📅 Due in {days} days"

        else:
            due_text = f"⚠ Overdue by {abs(days)} days"

        formatted_assignments.append(
            (title, due_text)
        )

    cursor.execute("""
    SELECT title
    FROM notes
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT 5
    """, (user_id,))

    recent_notes = cursor.fetchall()

    conn.close()

    return render_template(
    "dashboard.html",
    fullname=fullname,
    notes_count=notes_count,
    assignments_count=assignments_count,
    total_pomodoros=total_pomodoros,
    completion_rate=completion_rate,
    upcoming_assignments=formatted_assignments,
    recent_notes=recent_notes,
    completed_assignments=completed_assignments,
    pending_assignments=pending_assignments,
    active_page="dashboard")

@app.route("/notes", methods=["GET", "POST"])
def notes():
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )
    user = cursor.fetchone()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        

        cursor.execute("""
        INSERT INTO notes(user_id, title, content)
        VALUES(?, ?, ?)""", (user[0], title, content)
        )

        conn.commit()
        conn.close()
        return redirect("/notes")

    cursor.execute("""
    SELECT * FROM notes
    WHERE user_id = ?""", (user[0],)
    )
    
    notes = cursor.fetchall()
    conn.close()
    
    return render_template("notes.html", notes=notes, active_page="notes")

@app.route("/edit_note/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):

    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )
    user = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM notes
    WHERE id = ?
    AND user_id = ?""", (note_id, user[0])
    )

    note = cursor.fetchone()

    if note is None:
        conn.close()
        flash("Note not found.", "warning")
        return redirect(url_for("notes"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        cursor.execute("""
        UPDATE notes
        SET title = ?, content = ?
        WHERE id = ?""", (title, content, note_id)
        )

        conn.commit()
        conn.close()
        return redirect("/notes")

    conn.close()
    return render_template("edit_note.html", note=note)

@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )

    user = cursor.fetchone()

    cursor.execute("""
    DELETE FROM notes
    WHERE id = ?
    AND user_id = ?""", (note_id, user[0])
    )

    conn.commit()
    conn.close()
    return redirect("/notes")

@app.route("/assignments", methods=["GET","POST"])
def assignments():
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )

    user = cursor.fetchone()

    if request.method == "POST":
        title = request.form["title"]
        subject = request.form["subject"]
        due_date = request.form["due_date"]
        status = "Pending"

        cursor.execute("""
        INSERT INTO assignments(user_id, title, subject, due_date, status, pomodoros_completed)
        VALUES (?, ?, ?, ?, ?, ?)""", (user[0], title, subject, due_date, status, 0)
        )

        conn.commit()
        conn.close()

        return redirect("/assignments")

    cursor.execute("""
        SELECT * FROM assignments
        WHERE user_id = ?""", (user[0],)
        )
    
    assignments = cursor.fetchall()

    assignment_with_progress = []
    for assignment in assignments:
        pomodoros = assignment[6]
        progress = (pomodoros / 10) * 100
        if progress > 100:
            progress = 100
        assignment_with_progress.append(assignment + (progress,))

    
    conn.close()
    return render_template("assignments.html", assignments=assignment_with_progress, active_page="assignments")

@app.route("/edit_assignment/<int:assignment_id>", methods=["GET","POST"])
def edit_assignment(assignment_id):
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )

    user = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM assignments
    WHERE id = ?
    AND user_id = ?""", (assignment_id, user[0])
    )

    assignment = cursor.fetchone()

    if assignment is None:
        conn.close()
        flash("Assignment not found.", "warning")
        return redirect(url_for("assignments"))

    if request.method == "POST":
        title = request.form["title"]
        subject = request.form["subject"]
        due_date = request.form["due_date"]

        cursor.execute("""
        UPDATE assignments
        SET title = ?, subject = ?, due_date = ?
        WHERE id = ?
        AND user_id = ?""", (title, subject, due_date, assignment_id, user[0])
        )

        conn.commit()
        conn.close()
        return redirect("/assignments")
    return render_template("edit_assignment.html", assignment=assignment)


@app.route("/delete_assignment/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )

    user = cursor.fetchone()

    cursor.execute("""
    DELETE FROM assignments
    WHERE id = ?
    AND user_id = ?""", (assignment_id, user[0])
    )

    conn.commit()
    conn.close()
    return redirect("/assignments")


@app.route("/toggle_assignment/<int:assignment_id>", methods=["POST"])
def toggle_assignment(assignment_id):
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session["email"],)
    )

    user = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM assignments
    WHERE id = ?
    AND user_id = ?""", (assignment_id, user[0])
    )

    assignment = cursor.fetchone()

    if assignment is None:
        conn.close()
        flash("Assignment not found.", "warning")
        return redirect(url_for("assignments"))

    if assignment[5] == "Pending":
        status = "Completed"
    else:
        status = "Pending"

    cursor.execute("""
    UPDATE assignments
    SET status = ?
    WHERE id = ?
    AND user_id = ?""", (status, assignment_id, user[0])
    )

    conn.commit()
    conn.close()
    return redirect("/assignments")

@app.route("/pomodoro")
def pomodoro():
    if not session.get("logged_in"):
        return redirect('/login')

    return render_template("pomodoro.html", assignment=None, active_page="pomodoro")


@app.route("/pomodoro/<int:assignment_id>")
def assignment_pomodoro(assignment_id):
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session['email'],)
    )

    user = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM assignments
    WHERE id = ? AND user_id = ?""", (assignment_id, user[0])
    )

    assignment = cursor.fetchone()
    conn.close()

    if assignment is None:
        flash("Assignment not found.", "warning")
        return redirect(url_for("assignments"))

    return render_template("pomodoro.html", assignment=assignment, active_page="pomodoro")

@app.route("/update_pomodoro", methods=["POST"])
def update_pomodoro():
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    data = request.get_json()
    assignment_id = data["assignment_id"]

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session['email'],)
    )

    user = cursor.fetchone()

    cursor.execute("""
    UPDATE assignments
    SET pomodoros_completed = pomodoros_completed + 1
    WHERE id = ? AND user_id = ?""", (assignment_id, user[0])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})
    
@app.route("/search")
def search():
    if not session.get("logged_in"):
        return redirect('/login')

    query = request.args.get("query")
    print(query)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM users
    WHERE email = ?""", (session['email'],)
    )

    user = cursor.fetchone()

    user_id = user[0]

    cursor.execute("""
    SELECT title, content
    FROM notes
    WHERE user_id = ?
    AND (
    title LIKE ?
    OR content LIKE ?
    )
    """, (user_id, f"%{query}%", f"%{query}%"))

    notes = cursor.fetchall()

    cursor.execute("""
    SELECT title, subject, due_date, status
    FROM assignments
    WHERE user_id = ?
    AND (
        title LIKE ?
        OR subject LIKE ?
    )
    """, (
        user_id,
        f"%{query}%",
        f"%{query}%"
    ))

    assignments = cursor.fetchall()

    conn.close()

    return render_template("search.html", query=query, notes=notes, assignments=assignments, active_page="dashboard")


@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html",
        active_page=""
    ), 404


@app.route("/profile")
def profile():
    if not session.get("logged_in"):
        return redirect('/login')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, fullname, email, last_login
    FROM users
    WHERE email = ?""", (session['email'],)
    )

    user = cursor.fetchone()
    user_id = user[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM notes
    WHERE user_id = ?""", (user_id,)
    )

    notes_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM assignments
    WHERE user_id = ?""", (user_id,)
    )

    assignment_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM assignments
    WHERE user_id = ? AND status = 'Completed'""", (user_id,)
    )

    completed = cursor.fetchone()[0]

    cursor.execute("""
    SELECT SUM(pomodoros_completed)
    FROM assignments
    WHERE user_id = ?""", (user_id,)
    )

    total_pomodoros = cursor.fetchone()[0]

    if assignment_count:
        completion_rate = round(completed / assignment_count * 100)
    else:
        completion_rate = 0

    conn.close()

    return render_template(
        "profile.html",
        fullname=user[1],
        email=user[2],
        last_login=user[3],
        notes_count=notes_count,
        assignment_count=assignment_count,
        total_pomodoros=total_pomodoros,
        completion_rate=completion_rate,
        active_page="profile"
    )

if __name__ == "__main__":
    app.run(debug=True)