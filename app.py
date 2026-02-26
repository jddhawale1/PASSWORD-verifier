from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import math
from zxcvbn import zxcvbn

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- DATABASE ----------------

def init_db():

    conn = sqlite3.connect("users.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT
    )
    """)

    conn.close()

init_db()


# ---------------- ENTROPY ----------------

def calculate_entropy(password):

    charset = 0

    if any(c.islower() for c in password):
        charset += 26

    if any(c.isupper() for c in password):
        charset += 26

    if any(c.isdigit() for c in password):
        charset += 10

    if any(c in "!@#$%^&*" for c in password):
        charset += 8

    if charset == 0:
        return 0

    return round(len(password) * math.log2(charset), 2)


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:

            session["user"] = username
            return redirect("/dashboard")

        else:

            return render_template("login.html", error="Invalid login")

    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")

        conn.execute(
            "INSERT INTO users VALUES (?,?)",
            (username,password)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "user" not in session:
        return redirect("/")

    strength=""
    entropy=""

    if request.method == "POST":

        password = request.form["password"]
        name = request.form["name"]
        pet = request.form["pet"]
        year = request.form["year"]

        result = zxcvbn(password)

        levels = ["Very Weak","Weak","Medium","Strong","Very Strong"]

        strength = levels[result["score"]]

        entropy = calculate_entropy(password)

        # wordlist generation
        patterns = ["123","007","2024"]

        words = [name, pet, year]

        wordlist = []

        for word in words:

            if word:

                wordlist.append(word)

                for p in patterns:
                    wordlist.append(word+p)

        with open("wordlist.txt","w") as f:

            for w in wordlist:
                f.write(w+"\n")

    return render_template(
        "dashboard.html",
        user=session["user"],
        strength=strength,
        entropy=entropy
    )


# ---------------- DOWNLOAD ----------------

@app.route("/download")
def download():

    return send_file("wordlist.txt", as_attachment=True)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect("/")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
