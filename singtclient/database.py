import random

import pkg_resources
from twisted.enterprise import adbapi
from twisted.logger import Logger

# Start a logger with a namespace for a particular subsystem of our application.
log = Logger("database")

class Database:
    def __init__(self, db_filename, context):

        # Note if database already exists
        database_exists = db_filename.is_file()

        # Callback for every connection that is established to the
        # database
        def setup_connection(connection):
            # Turn on foreign key constraints
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Open a connection to the database.  SQLite will create the file if
        # it doesn't already exist.
        self.dbpool = adbapi.ConnectionPool(
            "sqlite3",
            db_filename,
            cp_openfun=setup_connection,
            check_same_thread=False # See https://twistedmatrix.com/trac/ticket/3629
        )

        # If the database did not exist, initialise the database
        if not database_exists:
            print("Database requires initialisation")
            self._d = self.dbpool.runInteraction(self._initialise_database)
            def on_success(data):
                log.info("Database successfully initialised")
            def on_error(data):
                log.error("Failed to initialise the database: "+str(data))
                reactor = context["reactor"]
                reactor.stop()

            self._d.addCallback(on_success)
            self._d.addErrback(on_error)

        
    # Initialise the database structure from instructions in file
    def _initialise_database(self, cursor):
        log.info("Initialising database")
        initialisation_commands_filename = pkg_resources.resource_filename(
            "singtclient",
            "database.sql"
        )
        f = open(initialisation_commands_filename, "r")
        initialisation_commands = f.read()
        cursor.executescript(initialisation_commands)

        # Create a randomly generated identifier.  It appears that a
        # sign bit is added by Python.
        bits_in_random_id = 63
        random_id = random.getrandbits(bits_in_random_id)
        cursor.execute(
            "INSERT INTO Settings (key, value) VALUES (?, ?)",
            ("client_id", random_id)
        )

        return random_id

    def get_client_id(self):
        def get_id(cursor):
            cursor.execute(
                "SELECT value FROM Settings WHERE key = ?",
                ("client_id",)
            )
            row = cursor.fetchone()
            if row is None:
                raise Exception("No client ID found in database")
            return row[0]
        
        return self.dbpool.runInteraction(get_id)
        
