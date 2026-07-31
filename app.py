from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "study_sync_secret"

@app.route('/')
def home():
    return render_template('index.html')

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
            return "Email does not exist"

        if check_password_hash(user[3], password):
            session["logged_in"] = True
            session["email"] = email
            conn.close()
            return redirect("/dashboard")
        else:
            conn.close()
            return "Incorrect password"
        

    return render_template("login.html")

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
            return "Email already exists"

        finally:
            conn.close()


        return redirect("/login")



    return render_template("signup.html")

@app.route('/dashboard')
def dashboard():

    if not session.get("logged_in"):
        return redirect("/login")


    return render_template("dashboard.html", email=session["email"])

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
    
    return render_template("notes.html", notes=notes)

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
        return "Note not found"

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
        INSERT INTO assignments(user_id, title, subject, due_date, status)
        VALUES (?, ?, ?, ?, ?)""", (user[0], title, subject, due_date, status)
        )

        conn.commit()
        conn.close()
        return redirect("/assignments")

    cursor.execute("""
    SELECT * FROM assignments
    WHERE user_id = ?""", (user[0],)
    )

    assignments = cursor.fetchall()
    conn.close()
    return render_template("assignments.html", assignments=assignments)

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
        return "Assignment not found"

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
        return "Assignment not found"

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


if __name__ == "__main__":
    app.run(debug=True)