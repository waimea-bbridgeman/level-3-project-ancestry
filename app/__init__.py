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

    # Select user info from db
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

    # Check if the username is available
    with connect_db() as db:
        sql = "SELECT id FROM users WHERE username=?"
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if user:
            flash(f"Username '{username}' already exists", "error")
            return redirect("/user/new")

        # Make a hash of their password and add everything to the db
        password_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (forename, surname, username, password_hash)
            VALUES (?, ?, ?, ?)
        """
        params = (forename, surname, username, password_hash)
        db.execute(sql, params)

        flash("Account created. Please login", "success")
        return redirect("/login")


# -----------------------------------------------------------
# Family Pick Page
# -----------------------------------------------------------
@app.get("/fam/pick")
@login_required
def select_family():
    with connect_db() as db:
        # Select users families
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
# Family Page
# -----------------------------------------------------------
@app.get("/fam/<int:id>")
@login_required
def show_family_home(id):
    with connect_db() as db:
        # Select chosen family
        sql = """
            SELECT families.id, families.surname, members.role
            FROM families
            JOIN members ON members.family_id = families.id
            WHERE families.id = ? AND members.user_id = ?
        """
        params = (id, session["user"]["id"])
        family = db.execute(sql, params).fetchone()

        # Make sure they're in the family
        if not family:
            flash(f"You're not in that family", "error")
            return redirect("/")

        # Populate the session with relevant data
        session["family"] = {
            "id": family["id"],
            "surname": family["surname"],
            "role": family["role"],
        }

        # Get the users stories from the family
        sql = """
            SELECT id, title, date, body, user_id
            FROM stories
            WHERE family_id = ? AND user_id = ?
        """
        params = (id, session["user"]["id"])
        stories = db.execute(sql, params).fetchall()

        # Get who is tagged in the stories
        sql = """
            SELECT involves.story_id, people.forename, people.surname
            FROM involves
            JOIN people ON people.id = involves.person_id
            WHERE people.family_id = ?
        """
        params = (id,)
        tagged = db.execute(sql, params).fetchall()

        return render_template(
            "pages/stories.jinja",
            family=family,
            stories=stories,
            tagged=tagged,
            title="My Stories",
        )


# -----------------------------------------------------------
# All Stories Page
# -----------------------------------------------------------
@app.get("/stories")
@login_required
def show_all_stories():
    # Check the user has selected a family
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Get story info
    with connect_db() as db:
        sql = """
            SELECT id, title, date, body, user_id
            FROM stories
            WHERE family_id = ?
        """
        params = (session["family"]["id"],)
        stories = db.execute(sql, params).fetchall()

        # Get who is tagged in the stories
        sql = """
            SELECT involves.story_id, people.forename, people.surname
            FROM involves
            JOIN people ON people.id = involves.person_id
            WHERE people.family_id = ?
        """
        params = (session["family"]["id"],)
        tagged = db.execute(sql, params).fetchall()

        return render_template(
            "pages/stories.jinja", stories=stories, tagged=tagged, title="All Stories"
        )


# -----------------------------------------------------------
# Create Family Page
# -----------------------------------------------------------
@app.get("/fam/new")
@login_required
def show_create_fam():
    return render_template("pages/create-fam.jinja")


# -----------------------------------------------------------
# Create Family
# -----------------------------------------------------------
@app.post("/fam/new")
@login_required
def create_fam():
    surname = request.form.get("surname", "").strip()

    # Create a 6 digit code for the family
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Add the code and family name to db
    with connect_db() as db:
        sql = """
            INSERT INTO families (surname, code)
            VALUES (?, ?)
        """
        params = (surname, code)
        db.execute(sql, params)

        # Find the ID of the new family
        sql = """
                SELECT id
                FROM families
                WHERE code = ?
        """
        params = (code,)
        family = db.execute(sql, params).fetchone()

        # Add the family creator as the owner
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
@login_required
def join_code_display():
    return render_template("pages/join-fam.jinja")


# -----------------------------------------------------------
# Process join form
# -----------------------------------------------------------
@app.post("/join-fam")
@login_required
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
        sql = "SELECT user_id FROM members WHERE family_id=? AND user_id=?"
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
@login_required
def join_fam():
    return render_template("pages/join-fam.jinja")


# -----------------------------------------------------------
# Add Person Page
# -----------------------------------------------------------
@app.get("/people/new")
@login_required
def add_person_page():
    return render_template("pages/add-person.jinja")


# -----------------------------------------------------------
# All People Page
# -----------------------------------------------------------
@app.get("/all-people")
@login_required
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
@login_required
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

    # Get the file selected from the form
    image = request.files.get("image", None)

    # Only save an image if one was chosen
    unique_filename = ""
    if image and image.filename != "":
        filename = secure_filename(image.filename)
        random_prefix = uuid.uuid4().hex[:12]
        unique_filename = f"{random_prefix}_{filename}"
        filepath = os.path.join(IMAGES_FOLDER, unique_filename)
        image.save(filepath)

    family_id = session["family"]["id"]

    # Add the form data and the upload filename to the DB
    with connect_db() as db:
        sql = """
            INSERT INTO people (forename, surname, dob, notes, image, links, user_id, family_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            forename,
            surname,
            dob,
            notes,
            unique_filename,
            links,
            session["user"]["id"],
            family_id,
        )
        db.execute(sql, params)

        flash("Person added", "success")
        return redirect("/all-people")


# -----------------------------------------------------------
# Show Story Form
# -----------------------------------------------------------
@app.get("/story")
@login_required
def show_story_form():
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    #
    with connect_db() as db:
        sql = """
            SELECT id, forename, surname
            FROM people
            WHERE family_id = ?
            ORDER BY forename
        """
        params = (session["family"]["id"],)
        people = db.execute(sql, params).fetchall()

    return render_template("pages/add-story.jinja", people=people)


# -----------------------------------------------------------
# Post Story
# -----------------------------------------------------------
@app.post("/story/new")
@login_required
def post_story():
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Get form data
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    date = request.form.get("date", "").strip()
    people_ids = request.form.getlist("people")

    # Validate data
    if not title:
        flash(f"Title is required", "error")
        return redirect("/story")

    if len(title) > 40:
        flash(f"Title is too long (max 40 chars)", "error")
        return redirect("/story")

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
        result = db.execute(sql, params)
        story_id = result.lastrowid

        # Tag each person who was ticked on the form
        for person_id in people_ids:
            sql = """
                INSERT INTO involves (story_id, person_id)
                VALUES (?, ?)
            """
            params = (story_id, person_id)
            db.execute(sql, params)

        flash("Story added", "success")
        return redirect(f"/fam/{family_id}")


# -----------------------------------------------------------
# Family Management
# -----------------------------------------------------------
@app.get("/family-admin")
@login_required
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

        # Select the relevant data from the db
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
@login_required
def delete_member(user_id):
    # Only allow the owner to remove members from the family
    if not session.get("family") or session["family"]["role"] != "owner":
        flash(f"Only the family owner can remove members", "error")
        return redirect("/")

    # Make sure the owner can't remove himself
    if user_id == session["user"]["id"]:
        flash(f"You can't remove yourself", "error")
        return redirect("/family-admin")

    # delete the member from the family
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
@login_required
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
# View a Single Person Page
# -----------------------------------------------------------
@app.get("/person/<int:id>")
@login_required
def show_person(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    family_id = session["family"]["id"]

    with connect_db() as db:
        sql = """
            SELECT id, forename, surname, dob, notes, image, links, user_id
            FROM people
            WHERE id = ? AND family_id = ?
        """
        params = (id, family_id)
        person = db.execute(sql, params).fetchone()

        if not person:
            flash(f"Person not found", "error")
            return redirect("/all-people")

        # Get the stories this person is tagged in
        sql = """
            SELECT stories.id, stories.title, stories.date, stories.body
            FROM stories
            JOIN involves ON involves.story_id = stories.id
            WHERE involves.person_id = ? AND stories.family_id = ?
        """
        params = (id, family_id)
        stories = db.execute(sql, params).fetchall()

        return render_template("pages/person.jinja", person=person, stories=stories)


# -----------------------------------------------------------
# Edit Person Page (only the user that added the person)
# -----------------------------------------------------------
@app.get("/person/<int:id>/edit")
@login_required
def show_person_edit_form(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    with connect_db() as db:
        sql = """
            SELECT id, forename, surname, dob, notes, links
            FROM people
            WHERE id = ? AND user_id = ? AND family_id = ?
        """
        params = (id, session["user"]["id"], session["family"]["id"])
        person = db.execute(sql, params).fetchone()

        if not person:
            flash(f"You can only edit people you added", "error")
            return redirect("/all-people")

        return render_template("pages/edit-person.jinja", person=person)


# -----------------------------------------------------------
# Update Person
# -----------------------------------------------------------
@app.post("/person/<int:id>")
@login_required
def update_person(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Get form data
    forename = request.form.get("forename", "").strip()
    surname = request.form.get("surname", "").strip()
    dob = request.form.get("dob", "").strip()
    notes = request.form.get("notes", "").strip()
    links = request.form.get("links", "").strip()

    # Validate data
    if not forename and not surname:
        flash(f"Enter at least a first or last name (even just 'Grandad')", "error")
        return redirect(f"/person/{id}/edit")

    # Escape text inputs
    forename = html.escape(forename)
    surname = html.escape(surname)
    dob = html.escape(dob)
    notes = html.escape(notes)
    links = html.escape(links)

    # Check the user added this person
    with connect_db() as db:
        sql = """
            SELECT id
            FROM people
            WHERE id = ? AND user_id = ? AND family_id = ?
        """
        params = (id, session["user"]["id"], session["family"]["id"])
        person = db.execute(sql, params).fetchone()

        if not person:
            flash(f"You can only edit people you added", "error")
            return redirect("/all-people")

        sql = """
            UPDATE people
            SET forename = ?, surname = ?, dob = ?, notes = ?, links = ?
            WHERE id = ?
        """
        params = (forename, surname, dob, notes, links, id)
        db.execute(sql, params)

        # Only change the image if a new one was chosen
        image = request.files.get("image", None)
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            random_prefix = uuid.uuid4().hex[:12]
            unique_filename = f"{random_prefix}_{filename}"
            filepath = os.path.join(IMAGES_FOLDER, unique_filename)
            image.save(filepath)

            sql = "UPDATE people SET image = ? WHERE id = ?"
            params = (unique_filename, id)
            db.execute(sql, params)

        flash("Person updated", "success")
        return redirect(f"/person/{id}")


# -----------------------------------------------------------
# Delete Person (only the person user that added the person)
# -----------------------------------------------------------
@app.get("/person/<int:id>/delete")
@login_required
def delete_person(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    with connect_db() as db:
        # Check the user added this person
        sql = """
            SELECT id
            FROM people
            WHERE id = ? AND user_id = ? AND family_id = ?
        """
        params = (id, session["user"]["id"], session["family"]["id"])
        person = db.execute(sql, params).fetchone()

        if not person:
            flash(f"You can only delete people you added", "error")
            return redirect("/all-people")

        # Remove them from any stories, then delete them
        sql = "DELETE FROM involves WHERE person_id = ?"
        params = (id,)
        db.execute(sql, params)

        sql = "DELETE FROM people WHERE id = ?"
        params = (id,)
        db.execute(sql, params)

        flash("Person deleted", "success")
        return redirect("/all-people")


# -----------------------------------------------------------
# Single Story Page
# -----------------------------------------------------------
@app.get("/story/<int:id>")
@login_required
def show_story(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    with connect_db() as db:
        sql = """
            SELECT stories.id, stories.title, stories.date, stories.body, stories.user_id,
                   users.forename, users.surname
            FROM stories
            JOIN users ON users.id = stories.user_id
            WHERE stories.id = ? AND stories.family_id = ?
        """
        params = (id, session["family"]["id"])
        story = db.execute(sql, params).fetchone()

        if not story:
            flash(f"Story not found", "error")
            return redirect("/stories")

        # Get who is tagged in the story
        sql = """
            SELECT people.id, people.forename, people.surname
            FROM involves
            JOIN people ON people.id = involves.person_id
            WHERE involves.story_id = ?
        """
        params = (id,)
        tagged = db.execute(sql, params).fetchall()

        return render_template("pages/story.jinja", story=story, tagged=tagged)


# -----------------------------------------------------------
# Edit Story Page (story's author only)
# -----------------------------------------------------------
@app.get("/story/<int:id>/edit")
@login_required
def show_story_edit_form(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    with connect_db() as db:
        sql = """
            SELECT id, title, date, body
            FROM stories
            WHERE id = ? AND user_id = ? AND family_id = ?
        """
        params = (id, session["user"]["id"], session["family"]["id"])
        story = db.execute(sql, params).fetchone()

        if not story:
            flash(f"You can only edit your own stories", "error")
            return redirect("/stories")

        # All the people in the family
        sql = """
            SELECT id, forename, surname
            FROM people
            WHERE family_id = ?
            ORDER BY forename
        """
        params = (session["family"]["id"],)
        people = db.execute(sql, params).fetchall()

        # The people already tagged in this story
        sql = """
            SELECT person_id
            FROM involves
            WHERE story_id = ?
        """
        params = (id,)
        tagged = db.execute(sql, params).fetchall()

        tagged_ids = []
        for row in tagged:
            tagged_ids.append(row["person_id"])

        return render_template(
            "pages/edit-story.jinja", story=story, people=people, tagged_ids=tagged_ids
        )


# -----------------------------------------------------------
# Update Story (story's author only)
# -----------------------------------------------------------
@app.post("/story/<int:id>")
@login_required
def update_story(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    # Get form data
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    date = request.form.get("date", "").strip()
    people_ids = request.form.getlist("people")

    # Validate data
    if not title:
        flash(f"Title is required", "error")
        return redirect(f"/story/{id}/edit")

    if len(title) > 40:
        flash(f"Title is too long (max 40 chars)", "error")
        return redirect(f"/story/{id}/edit")

    # Escape text inputs
    title = html.escape(title)
    body = html.escape(body)
    date = html.escape(date)

    with connect_db() as db:
        # Check it is the user's own story
        sql = """
            SELECT id
            FROM stories
            WHERE id = ? AND user_id = ? AND family_id = ?
        """
        params = (id, session["user"]["id"], session["family"]["id"])
        story = db.execute(sql, params).fetchone()

        if not story:
            flash(f"You can only edit your own stories", "error")
            return redirect("/stories")

        sql = """
            UPDATE stories
            SET title = ?, body = ?, date = ?
            WHERE id = ?
        """
        params = (title, body, date, id)
        db.execute(sql, params)

        # Replace the tagged people with the ones ticked now
        sql = "DELETE FROM involves WHERE story_id = ?"
        params = (id,)
        db.execute(sql, params)

        for person_id in people_ids:
            sql = "INSERT INTO involves (story_id, person_id) VALUES (?, ?)"
            params = (id, person_id)
            db.execute(sql, params)

        flash("Story updated", "success")
        return redirect(f"/story/{id}")


# -----------------------------------------------------------
# Delete Story (story's author only)
# -----------------------------------------------------------
@app.get("/story/<int:id>/delete")
@login_required
def delete_story(id):
    if not session.get("family"):
        flash(f"Pick or create a family first", "error")
        return redirect("/")

    with connect_db() as db:
        # Check it is the user's own story
        sql = """
            SELECT id
            FROM stories
            WHERE id = ? AND user_id = ? AND family_id = ?
        """
        params = (id, session["user"]["id"], session["family"]["id"])
        story = db.execute(sql, params).fetchone()

        if not story:
            flash(f"You can only delete your own stories", "error")
            return redirect("/stories")

        # Remove the tags, then the story
        sql = "DELETE FROM involves WHERE story_id = ?"
        params = (id,)
        db.execute(sql, params)

        sql = "DELETE FROM stories WHERE id = ?"
        params = (id,)
        db.execute(sql, params)

        flash("Story deleted", "success")
        return redirect(f"/fam/{session['family']['id']}")


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