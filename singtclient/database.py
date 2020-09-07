import random

import pkg_resources
from twisted.internet import defer
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
        dbpool = adbapi.ConnectionPool(
            "sqlite3",
            db_filename,
            cp_openfun=setup_connection,
            check_same_thread=False # See https://twistedmatrix.com/trac/ticket/3629
        )

        # If the database did not exist, initialise the database
        if not database_exists:
            log.info("Database requires initialisation")
            self._db_ready = dbpool.runInteraction(self._initialise_database)
            def on_success(data):
                log.info("Database successfully initialised")
                return dbpool
            def on_error(data):
                log.error("Failed to initialise the client's database: "+str(data))
                reactor = context["reactor"]
                reactor.stop()

            self._db_ready.addCallback(on_success)
            self._db_ready.addErrback(on_error)
        else:
            # Database exists already
            self._db_ready = defer.Deferred()
            self._db_ready.callback(dbpool)

        # Check that database is the correct version
        expected_version = 1
        def check_version(cursor):
            cursor.execute("SELECT version FROM Version")
            row = cursor.fetchone()
            if row is None:
                raise Exception("No version found in Version table of database")
            if row[0] == expected_version:
                log.info(f"Client database version {expected_version}")
                return dbpool
            else:
                raise Exception(f"Database version ({row[0]}) did not match expected version ({expected_version})")

        def run_check_version(dbpool):
            return dbpool.runInteraction(check_version)
        self._db_ready.addCallback(run_check_version)

        def on_error(error):
            log.error("Failed to verify the database: "+str(error))
            reactor = context["reactor"]
            reactor.stop()
        self._db_ready.addErrback(on_error)

            
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

        def when_ready(dbpool):
            return dbpool.runInteraction(get_id)
        def on_error(error):
            log.warn("Failed to get client id: "+str(error))
            return error

        d = self._db_ready
        d.addCallback(when_ready)
        d.addErrback(on_error)

        return d
