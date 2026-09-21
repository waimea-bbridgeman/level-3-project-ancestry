#============================================================================
# Database schema and seed data configuration
#============================================================================


#----------------------------------------------------------------------------
# Table definitions
#----------------------------------------------------------------------------
# Define your tables with a name, a schema and optional seed/sample data,
# using this format, and then add the tables to the Table Registry below:
#
# class TableName:
#     NAME      = "name"
#     SCHEMA    = "CREATE TABLE name (...)"
#     SEED_DATA = "INSERT INTO name (...)" or None
#----------------------------------------------------------------------------
class UserTable:

    NAME = "users"

    SCHEMA = """ 
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forename TEXT NOT NULL,
            surname TEXT NOT NULL, 
            username TEXT NOT NULL UNIQUE, 
            password_hash TEXT NOT NULL
        )
    """


    SEED_DATA = """
        INSERT INTO users (forename, surname, username, password_hash)
        VALUES ("Test", "User", "test", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252")
    """


class PeopleTable:

    NAME = "people"

    SCHEMA = """ 
        CREATE TABLE people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forename TEXT NOT NULL,
            surname TEXT NOT NULL, 
            notes TEXT, 
            dob TEXT
        )
    """


    SEED_DATA = """
        INSERT INTO people (forename, surname)
        VALUES ("Johnny", "Pigman")
    """
class InvolvesTable:

    NAME = "involves"

    SCHEMA = """ 
        CREATE TABLE involves (
            story_id,
            person_id
        )
    """


    SEED_DATA = """
        
    """


class ImagesTable:

    NAME = "images"

    SCHEMA = """ 
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            story_id INTEGER
        )
    """


    SEED_DATA = """
         INSERT INTO images (filename, story_id)
        VALUES ("docs/evidence/screenshots/V1.png", "1")
    """

class StoryTable:

    NAME = "stories"

    SCHEMA = """
        CREATE TABLE stories (
            id  INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT NOT NULL, 
            body    TEXT NOT NULL,
            date    TEXT,

            user_id INTEGER NOT NULL,
            
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """

    SEED_DATA = """
        INSERT INTO stories (user_id, title, body, date)
        VALUES
            ("1", "Treacherous Journey", "The journey was treacherous.", "2025-12-12")
    """

class FamiliesTable:

    NAME = "families"

    SCHEMA = """ 
        CREATE TABLE families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            surname TEXT NOT NULL
        )
    """


    SEED_DATA = """
         INSERT INTO families (code, surname)
        VALUES ("XTTYVB", "Williams")
    """

# Add more table classes here...



#----------------------------------------------------------------------------
# Table registry
#----------------------------------------------------------------------------
# Register all of your tables by adding them to the TABLES list here:
#
# TABLES = [
#     Table1Name,
#     Table2Name,
#     etc.
# ]
#
# Note: The table order is important - Create the tables that have
# foreign keys *after* the tables they link to have been created
#----------------------------------------------------------------------------

TABLES = [
    PeopleTable, 
    InvolvesTable,
    ImagesTable,
    StoryTable,
    UserTable,
    FamiliesTable,
    # Add more tables here...
]

