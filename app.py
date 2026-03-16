from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secretkey"

# Folder for uploaded images
IMAGE_FOLDER = "static/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------- Database setup ----------
def init_db():
    # Users table
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # Photos table
    conn = sqlite3.connect("gallery.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# ---------- Database functions ----------
def get_user(username, password=None):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    if password:
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    else:
        c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users(username,password) VALUES (?,?)", (username, password))
    conn.commit()
    conn.close()

def get_photos(user_id):
    conn = sqlite3.connect("gallery.db")
    c = conn.cursor()
    c.execute("SELECT id, filename, title FROM photos WHERE user_id=?", (user_id,))
    photos = c.fetchall()
    conn.close()
    return photos

def add_photo(filename, title, user_id):
    conn = sqlite3.connect("gallery.db")
    c = conn.cursor()
    c.execute("INSERT INTO photos(filename,title,user_id) VALUES(?,?,?)", (filename, title, user_id))
    conn.commit()
    conn.close()

def delete_photo(photo_id):
    conn = sqlite3.connect("gallery.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM photos WHERE id=?", (photo_id,))
    result = c.fetchone()
    if result:
        file = result[0]
        path = os.path.join(IMAGE_FOLDER, file)
        if os.path.exists(path):
            os.remove(path)
    c.execute("DELETE FROM photos WHERE id=?", (photo_id,))
    conn.commit()
    conn.close()

# ---------- Routes ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user(username, password)
        if user:
            session["user_id"] = user[0]
            return redirect(url_for("gallery"))
        else:
            return "Invalid login"
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            add_user(username, password)
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists"
    return render_template("signup.html")

@app.route("/gallery", methods=["GET","POST"])
def gallery():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    if request.method == "POST":
        file = request.files.get("photo")
        title = request.form.get("title", "")
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join(IMAGE_FOLDER, filename))
            add_photo(filename, title, user_id)
    photos = get_photos(user_id)
    return render_template("gallery.html", photos=photos)

@app.route("/delete/<int:photo_id>")
def delete(photo_id):
    delete_photo(photo_id)
    return redirect(url_for("gallery"))

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

# ---------- Main ----------
if __name__ == "__main__":
    init_db()  # Create tables if they don't exist
    import os
    port = int(os.environ.get("PORT", 5000))  # Dynamic port for Render
    app.run(host="0.0.0.0", port=port)