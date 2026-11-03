# ===========================================================
# Ancestry Tracker
# By Billy Bridgeman
# ===========================================================
import random
import string
from flask import (
    Flask,
    request,
    session,
    render_template,
    flash,
    redirect,
    send_file,
    make_response,
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from io import BytesIO
import html
from app.helpers import *
import os
import uuid
from werkzeug.utils import secure_filename

IMAGES_FOLDER = os.path.join("app", "static", "images")

# Create the app
app = Flask(__name__)


# ===========================================================
# App Routes Handlers
# ===========================================================


# -----------------------------------------------------------
# Home page
# -----------------------------------------------------------
@app.get("/")
def show_home():
    # If user is logged in show their families
    if session.get("logged_in"):
        return redirect("/fam/pick")
    else:
        return redirect("/login")


# -----------------------------------------------------------
# Login Page
# -----------------------------------------------------------
@app.get("/login")
def show_login_form():
    return render_template("pages/login.jinja")


# -----------------------------------------------------------
# Login User
# -----------------------------------------------------------
@app.post("/login")
def login_user():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "").strip()

    with connect_db() as db:
        sql = """
            SELECT id, forename, surname, password_hash
            FROM users
            WHERE username=?
        """
        params = (username,)
        user = db.execute(sql, params).fetchone()

        # Check for user
        if not user:
            flash(f"Unknown user", "error")
            return redirect("/login")

        # Check password hash
        if not check_password_hash(user["password_hash"], password):
            flash(f"Incorrect password", "error")
            return redirect("/login")

        session["logged_in"] = True
        session["user"] = {
            "username": username,
            "forename": user["forename"],
            "surname": user["surname"],
            "id": user["id"],
        }

        flash("Login successful", "success")
        return redirect("/")


# -----------------------------------------------------------
# Sign-up Page
# -----------------------------------------------------------
@app.get("/user/new")
def show_signup_form():
    return render_template("pages/sign-up.jinja")


# -----------------------------------------------------------
# Sign-up User
# -----------------------------------------------------------
@app.post("/user")
def process_new_user():
    forename = request.form.get("forename", "").strip()
    surname = request.form.get("surname", "").strip()
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "").strip()

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


# -----------------------------------------------------------
# Family Pick Page
# -----------------------------------------------------------
@app.get("/fam/pick")
def select_family():
    with connect_db() as db:
        sql = """
            SELECT families.id, families.surname, members.role
            FROM members
            JOIN families ON families.id = members.family_id
            WHERE members.user_id = ?
        """
        params = (session["user"]["id"],)
        families = db.execute(sql, params).fetchall()

        return render_template("pages/family-pick.jinja", families=families)


# -----------------------------------------------------------
# Stories Page
# -----------------------------------------------------------
@app.get("/fam/<int:id>")
def show_family_home(id):
    with connect_db() as db:
        sql = """
            SELECT families.id, families.surname, members.role
            FROM families
            JOIN members ON members.family_id = families.id
            WHERE families.id = ? AND members.user_id = ?
        """
        params = (id, session["user"]["id"])
        family = db.execute(sql, params).fetchone()

        # Are they  already in the family?
        if not family:
            flash(f"You're not in that family", "error")
            return redirect("/")

        session["family"] = {
            "id": family["id"],
            "surname": family["surname"],
            "role": family["role"],
        }

        sql = """
            SELECT id, title, date, body
            FROM stories
            WHERE family_id = ? AND user_id = ?
        """
        params = (id, session["user"]["id"])
        stories = db.execute(sql, params).fetchall()

        return render_template(
            "pages/stories.jinja", family=family, stories=stories, title="My Stories"
        )


# -----------------------------------------------------------
# All Stories Page
# -----------------------------------------------------------
@app.get("/stories")
def show_all_stories():
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    with connect_db() as db:
        sql = """
            SELECT id, title, date, body
            FROM stories
            WHERE family_id = ?
        """
        params = (session["family"]["id"],)
        stories = db.execute(sql, params).fetchall()

        return render_template(
            "pages/stories.jinja", stories=stories, title="All Stories"
        )


# -----------------------------------------------------------
# Create Family Page
# -----------------------------------------------------------
@app.get("/fam/new")
def show_create_fam():
    return render_template("pages/create-fam.jinja")


# -----------------------------------------------------------
# Create Family
# -----------------------------------------------------------
@app.post("/fam/new")
def create_fam():
    surname = request.form.get("surname", "").strip()

    # Create a 6 didget code for the family
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # add the code and family name to db
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


# -----------------------------------------------------------
# Join Code Page
# -----------------------------------------------------------
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

    return render_template("pages/join-fam.jinja", code=code)


# -----------------------------------------------------------
# Process join form
# -----------------------------------------------------------
@app.post("/join-fam")
def join_code():

    # Get form data
    code = request.form.get("code", "").strip().upper()
    user_id = session["user"]["id"]

    # Check if valid
    if not code:
        flash(f"Family code is required", "error")
        return redirect("/join-fam")

    if len(code) != 6:
        flash(f"Family code must be 6 characters", "error")
        return redirect("/join-fam")

    with connect_db() as db:
        # Find the family with this code
        sql = "SELECT id FROM families WHERE code=?"
        params = (code,)
        family = db.execute(sql, params).fetchone()

        if not family:
            flash(f"No family found", "error")
            return redirect("/join-fam")

        family_id = family["id"]

        # Check they are not already a member
        sql = "SELECT id FROM members WHERE family_id=? AND user_id=?"
        params = (family_id, user_id)
        member = db.execute(sql, params).fetchone()

        if member:
            flash(f"You're already in that family", "error")
            return redirect("/join-fam")

        # Add them to the family
        sql = """
            INSERT INTO members (family_id, user_id, role)
            VALUES (?, ?, ?)
        """
        params = (family_id, user_id, "member")
        db.execute(sql, params)

        flash("You've joined the family!", "success")
        return redirect("/")


# -----------------------------------------------------------
# Join Family Page
# -----------------------------------------------------------
@app.get("/join-fam")
def join_fam():
    return render_template("pages/join-fam.jinja")


# -----------------------------------------------------------
# Add Person Page
# -----------------------------------------------------------
@app.get("/people/new")
def add_person_page():
    return render_template("pages/add-person.jinja")


# -----------------------------------------------------------
# All People Page
# -----------------------------------------------------------
@app.get("/all-people")
def show_people():
    # Check if the session has a family selected
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Get info about a person
    with connect_db() as db:
        sql = """
            SELECT id, forename, surname, image
            FROM people
            WHERE family_id = ?
            ORDER BY forename
        """
        params = (session["family"]["id"],)
        people = db.execute(sql, params).fetchall()

        return render_template("pages/all-people.jinja", people=people)


# -----------------------------------------------------------
# Add Person
# -----------------------------------------------------------
@app.post("/person")
def add_persondb():
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Get the normal text fields from the form
    forename = request.form.get("forename", "").strip()
    surname = request.form.get("surname", "").strip()
    dob = request.form.get("dob", "").strip()
    notes = request.form.get("notes", "").strip()
    links = request.form.get("links", "").strip()

    # Validate data
    if not forename and not surname:
        flash(f"Enter at least a first or last name (even just 'Grandad')", "error")
        return redirect("/people/new")

    forename = html.escape(forename)
    surname = html.escape(surname)
    dob = html.escape(dob)
    notes = html.escape(notes)
    links = html.escape(links)

    # Get the file selected via the form
    image = request.files.get("image", None)
    if not image or image.filename == "":
        flash(f"There was a problem uploading the image", "error")
        return redirect("/people/new")

    # Sanitise filename and make it unique
    filename = secure_filename(image.filename)
    random_prefix = uuid.uuid4().hex[:12]
    unique_filename = f"{random_prefix}_{filename}"

    # Get the path of the upload folder
    filepath = os.path.join(IMAGES_FOLDER, unique_filename)

    # Save file to disk
    image.save(filepath)

    family_id = session["family"]["id"]

    # Add the form data and the upload filename to the DB
    with connect_db() as db:
        sql = """
            INSERT INTO people (forename, surname, dob, notes, image, links, family_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (forename, surname, dob, notes, unique_filename, links, family_id)
        db.execute(sql, params)

        flash("Person added", "success")
        return redirect("/all-people")


# -----------------------------------------------------------
# Show Story Form
# -----------------------------------------------------------
@app.get("/story")
def show_story_form():
    return render_template("pages/add-story.jinja")


# -----------------------------------------------------------
# Post Story
# -----------------------------------------------------------
@app.post("/story/new")
def post_story():

    # Get form data
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    date = request.form.get("date", "").strip()

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
    family_id = session["family"]["id"]

    # Add to database
    with connect_db() as db:
        sql = """
            INSERT INTO stories (title, body, date, user_id, family_id)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (title, body, date, user_id, family_id)
        db.execute(sql, params)

    flash("Story added")
    return redirect(f"/fam/{family_id}")


# -----------------------------------------------------------
# Family Management
# -----------------------------------------------------------
@app.get("/family-admin")
def manage_fam():
    # Check there is a family in the session
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    family_id = session["family"]["id"]

    with connect_db() as db:
        sql = """
            SELECT id, surname, code
            FROM families
            WHERE id = ?
        """
        params = (family_id,)
        family = db.execute(sql, params).fetchone()

        sql = """
            SELECT users.id AS user_id, users.forename, users.surname, members.role
            FROM members
            JOIN users ON users.id = members.user_id
            WHERE members.family_id = ?
        """
        params = (family_id,)
        members = db.execute(sql, params).fetchall()

        return render_template(
            "pages/family-admin.jinja", family=family, members=members
        )


# -----------------------------------------------------------
# Remove member (owner use)
# -----------------------------------------------------------
@app.get("/member/<int:user_id>/delete")
def delete_member(user_id):
    # Only allow the owner to remove members from the family
    if not session.get("family") or session["family"]["role"] != "owner":
        flash(f"Only the family owner can remove members", "error")
        return redirect("/")

    # Make sure the owner can't remove himself
    if user_id == session["user"]["id"]:
        flash(f"You can't remove yourself", "error")
        return redirect("/family-admin")

    # delete the memeber from the family
    with connect_db() as db:
        sql = """
            DELETE FROM members
            WHERE family_id = ? AND user_id = ?
        """
        params = (session["family"]["id"], user_id)
        db.execute(sql, params)

        flash(f"Member removed", "success")
        return redirect("/family-admin")


# -----------------------------------------------------------
# Leave a Family (member use)
# -----------------------------------------------------------
@app.get("/family/leave")
def leave_family():
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Can't leave a family ownerless
    if session["family"]["role"] == "owner":
        flash(f"The owner can't leave the family", "error")
        return redirect("/family-admin")

    with connect_db() as db:
        sql = """
            DELETE FROM members
            WHERE family_id = ? AND user_id = ?
        """
        params = (session["family"]["id"], session["user"]["id"])
        db.execute(sql, params)

    # Remove the family from the session data
    session.pop("family", None)
    flash(f"You have left the family", "success")
    return redirect("/")


# -----------------------------------------------------------
# Logout
# -----------------------------------------------------------
@app.get("/logout")
def logout_user():
    # Clear the session
    session.clear()
    flash(f"You have been logged out", "success")
    return redirect("/")


# ===========================================================
# Configure the app
# ===========================================================
load_dotenv()
app.config.from_prefixed_env()
init_logging(app)
init_text_filters(app)
init_date_filters(app)
init_error_handlers(app)
init_database()
register_commands(app)
