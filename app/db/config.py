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

class NoteTable:

    NAME = "note"

    SCHEMA = """
        CREATE TABLE note (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT NOT NULL,
            body    TEXT,
            pinned  INTEGER DEFAULT 0,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    SEED_DATA = """
        INSERT INTO note (title, pinned, body)
        VALUES
            ("Welcome!",      1, "This is a demo application using Flask, Jinja and SQLite."),
            ("Shopping List", 0, "Milk\nBread\nEggs\nCheese"),
            ("Meeting Notes", 0, "Discussed project timeline.\n\nAction items:\n- Review design\n- Update docs"),
            ("Recipe: Pasta", 0, "Ingredients:\n- 500g pasta\n- Tomato sauce\n- Garlic\n\nCook pasta, add sauce, enjoy!"),
            ("Important!",    1, "Remember to backup your database regularly.")
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
    NoteTable,
    # Add more tables here...
]

