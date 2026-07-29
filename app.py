from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "study_sync_secret"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        session["logged_in"] = True
        session["email"] = email

        password = request.form["password"]

        print(email)
        print(password)

        return redirect("/dashboard")

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

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()


        try:
            cursor.execute("""
                        INSERT INTO users(fullname, email, password)
                        VALUES(?, ?, ?)""", (fullname, email, password))
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

if __name__ == "__main__":
    app.run(debug=True)