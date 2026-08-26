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

class StoryTable:

    NAME = "story"

    SCHEMA = """
        CREATE TABLE story (
            id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title   TEXT NOT NULL, 
            body    TEXT NOT NULL,
            date    TEXT

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """

    SEED_DATA = """
        INSERT INTO story (title, body)
        VALUES
            ("Treacherous Journey", "The journey was treacherous.")
    """

# Add more table classes here...

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


# class FamilyTable:

#     NAME = "users"

#     SCHEMA = """ 
#         CREATE TABLE users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             forename TEXT NOT NULL,
#             surname TEXT NOT NULL, 
#             username TEXT NOT NULL UNIQUE, 
#             password_hash TEXT NOT NULL
#         )
#     """


#     SEED_DATA = """
#         INSERT INTO users (forename, surname, username, password_hash)
#         VALUES ("Test", "User", "test", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252")
#     """
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
    StoryTable,
    UserTable,
    # Add more tables here...
]

