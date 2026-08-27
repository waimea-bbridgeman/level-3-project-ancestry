#===========================================================
# PROJECT NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from io import BytesIO
import html
from app.helpers import *


# Create the app
app = Flask(__name__)


#===========================================================
# App Routes Handlers
#===========================================================

#-----------------------------------------------------------
# Home page - Logged in
#-----------------------------------------------------------
@app.get("/homelog")
def show_homelog():
    with connect_db() as db:
        sql = """
            SELECT forename
            FROM users
        """
        params = ()
        users = db.execute(sql, params).fetchall()


    return render_template("pages/homelog.jinja", users=users)


#-----------------------------------------------------------
# Home page - Not logged in 
#-----------------------------------------------------------
@app.get("/")
def show_home():

    return render_template("pages/home.jinja") 



#-----------------------------------------------------------
# Login page
#-----------------------------------------------------------

@app.get("/login")
def show_login_form():
    return render_template("pages/login.jinja")

#-----------------------------------------------------------
# Login user 
#-----------------------------------------------------------
@app.post("/login")
def login_user():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = """
            SELECT id, forename, surname, password_hash
            FROM users
            WHERE username=?
        """
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if not user:
            flash(f"Unknown user", "error")
            return redirect("/login")

        if not check_password_hash(user["password_hash"], password):
            flash(f"Incorrect password", "error")
            return redirect("/login")

        session["logged_in"] = True
        session["user"] = {
            "username": username,
            "forename": user["forename"],
            "surname":  user["surname"],
            "id":       user["id"]
        }

        flash("Login successful", "success")
        return redirect("/homelog")

#-----------------------------------------------------------
# Sign-up page 
#-----------------------------------------------------------
@app.get("/user/new")
def show_signup_form():
    return render_template("pages/sign-up.jinja")

#-----------------------------------------------------------
# Sign-up user 
#-----------------------------------------------------------
@app.post("/user")
def process_new_user():
    forename = request.form.get('forename', '').strip()
    surname  = request.form.get('surname',  '').strip()
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = "SELECT id FROM users WHERE username=?"
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if user:
            flash(f"Username '{username}' already exists", "error")
            return redirect("/user/new")

        password_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (forename, surname, username, password_hash)
            VALUES (?, ?, ?, ?)
        """
        params = (forename, surname, username, password_hash)
        db.execute(sql, params)

        flash("Account created. Please login", "success")
        return redirect("/homelog")
   
#-----------------------------------------------------------
# Show Story Form
#-----------------------------------------------------------
@app.get("/story/new")
def show_story_form():
    return render_template("pages/story_form.jinja")

#-----------------------------------------------------------
# Post story
#-----------------------------------------------------------
@app.post("/story")
def post_story():

    # Get form data
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    # Validate data
    if not title:
        flash("Title is required", "error")
        return redirect("/story/new")

    if len(title) > 40:
        flash("Title is too long (max 40 chars)", "error")
        return redirect("/story/new")

    # Escape text inputs
    title = html.escape(title)
    body = html.escape(body)

    user_id = session["user"]["id"]

    # Add to database
    with connect_db() as db:
        sql = """
            INSERT INTO story (title, body, user_id)
            VALUES (?, ?, ?)
        """
        params = (title, body, user_id)
        db.execute(sql, params)

    flash(f"Story added")
    return redirect("/homelog")


#-----------------------------------------------------------
# Logout
#-----------------------------------------------------------
@app.get("/logout")
def logout_user():
    session.clear()
    flash(f"You have been logged out", "success")
    return redirect("/")
#===========================================================
# Configure the app
#===========================================================
load_dotenv()
app.config.from_prefixed_env()
init_logging(app)
init_text_filters(app)
init_date_filters(app)
init_error_handlers(app)
init_database()
register_commands(app)

