#===========================================================
# Ancestry Tracker
# By Billy Bridgeman
#===========================================================
import random
import string
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
# Home page 
#-----------------------------------------------------------
@app.get("/")
def show_home():

    if session.get("logged_in"):
        return redirect("/fam/pick")
    else:
        return redirect("/login") 


#-----------------------------------------------------------
# Login Page
#-----------------------------------------------------------

@app.get("/login")
def show_login_form():
    return render_template("pages/login.jinja")

#-----------------------------------------------------------
# Login User 
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
        return redirect("/")

#-----------------------------------------------------------
# Sign-up Page 
#-----------------------------------------------------------
@app.get("/user/new")
def show_signup_form():
    return render_template("pages/sign-up.jinja")

#-----------------------------------------------------------
# Sign-up User 
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
        return redirect("/")
#-----------------------------------------------------------
# Family Pick Page
#-----------------------------------------------------------
@app.get("/fam/pick")
def select_family():
    with connect_db() as db:
        sql = """ 
            SELECT 
                *
            FROM families
        """
        params = ()
        families = db.execute(sql, params).fetchall()

        return render_template("pages/family-pick.jinja", families=families)
    
    
#-----------------------------------------------------------
# Stories Page
#-----------------------------------------------------------
@app.get("/fam/<int:id>")
def show_family_home(id):
    with connect_db() as db:
        sql = """ 
            SELECT *
            FROM families
            WHERE id=?
        """
        params = (id,)
        family = db.execute(sql, params).fetchone()

        sql = """ 
             SELECT 
                stories.id, 
                stories.title, 
                stories.date,
                stories.body

            FROM stories
            JOIN members ON members.user_id = stories.user_id
            WHERE members.family_id = ?
            
        """  

        params = ()
        stories = db.execute(sql, params).fetchall()

        return render_template("pages/stories.jinja", family=family, stories=stories)
    
#-----------------------------------------------------------
# Stories Page
#-----------------------------------------------------------
@app.get("/stories")
def show_all_stories():
    with connect_db() as db:
        sql = """ 
            SELECT 
                stories.id, 
                stories.title, 
                stories.date,
                stories.body

            FROM stories
        """
        params = ()
        stories = db.execute(sql, params).fetchall()

        return render_template("pages/stories.jinja", stories=stories)
#-----------------------------------------------------------
# Create Family Page
#-----------------------------------------------------------
@app.get("/fam/new")
def show_create_fam():
    return render_template("pages/create-fam.jinja")
#-----------------------------------------------------------
# Create Family 
#-----------------------------------------------------------
@app.post("/fam/new")
def create_fam():
    surname  = request.form.get('surname',  '').strip()
   
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    with connect_db() as db:
        sql = """
            INSERT INTO families (surname, code)
            VALUES (?, ?)
        """
        params = (surname, code)
        db.execute(sql, params)

        sql = """
                SELECT id
                FROM families
                WHERE code = ?
        """
        params = (code,)
        family = db.execute(sql, params).fetchone()

        sql = """
            INSERT INTO members (family_id, user_id, role)
            VALUES (?, ?, ?)
        """
        params = (family["id"], session["user"]["id"], "owner")
        db.execute(sql, params)

        flash(f"Family created! Your family code is {code}", "success")
        
    return redirect("/")
#-----------------------------------------------------------
# Join Code Page
#-----------------------------------------------------------
@app.get("/join/new")
def join_code_display():
    with connect_db() as db:
        sql = """
            SELECT families.code
            FROM families
            JOIN members ON members.family_id = families.id
            WHERE members.user_id = ?
        """
        params = (session["user"]["id"],)
        code = db.execute(sql, params).fetchone()

    return render_template("pages/join-code.jinja", code=code)

#-----------------------------------------------------------
# Join Family - process join code form
#-----------------------------------------------------------
@app.post("/join-fam")
def join_code():
    user_id = session["user"]["id"]
    code = request.form.get("code", "").strip().upper()

    with connect_db() as db:
        family = db.execute(
            "SELECT id FROM families WHERE code = ?", (code,)
        ).fetchone()

        if family:
            family_id = family["id"]

            existing = db.execute(
                "SELECT id FROM members WHERE family_id = ? AND user_id = ?",
                (family_id, user_id),
            ).fetchone()

            if existing:
                flash("You're already in that family", "error")
                return redirect("/join-fam")

            db.execute(
                "INSERT INTO members (family_id, user_id, role) VALUES (?, ?, ?)",
                (family_id, user_id, "member"),
            )
            flash("You've joined the family!", "success")
            return redirect("/")

        else:
            flash("No family found", "error")
            return redirect("/")
#-----------------------------------------------------------
# Join Family Page
#-----------------------------------------------------------
@app.get("/join-fam")
def join_fam():
    return render_template("pages/join-fam.jinja")


#-----------------------------------------------------------
# Add Person Page
#-----------------------------------------------------------
@app.get("/people/new")
def add_person():
    return render_template("pages/add-person.jinja")

#-----------------------------------------------------------
# Show Story Form
#-----------------------------------------------------------
@app.get("/story")
def show_story_form():
    return render_template("pages/story-form.jinja")

#-----------------------------------------------------------
# Post Story
#-----------------------------------------------------------
@app.post("/story/new")
def post_story():

    # Get form data
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    date = request.form.get('date', '').strip()
    

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
    date = html.escape(date)

    user_id = session["user"]["id"]

    # Add to database
    with connect_db() as db:
        sql = """
            INSERT INTO stories (title, body, date, user_id)
            VALUES (?, ?, ?, ?)
        """
        params = (title, body, date, user_id)
        db.execute(sql, params)

    flash(f"Story added")
    return redirect("/")

#-----------------------------------------------------------
# Family Management
#-----------------------------------------------------------
@app.get("/family-admin")
def manage_fam():
    return render_template("pages/family-admin.jinja")

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

