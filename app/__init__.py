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
        return redirect("/")
    
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

