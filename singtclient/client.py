import copy
from pathlib import Path
import random
import sys
import threading
import webbrowser

import art
import numpy
import pkg_resources
import sounddevice as sd
from twisted.internet import reactor
from twisted.logger import Logger, LogLevel, LogLevelFilterPredicate, \
    textFileLogObserver, FilteringLogObserver, globalLogBeginner

from .client_web import create_web_interface
from .command import Command
from .database import Database
from .session_files import SessionFiles
from .client_udp import UDPClient

# Start a logger with a namespace for a particular subsystem of our application.
log = Logger("client")

def init_session(context):
    root = context["root"]
    # Setup directory for session
    session_files = SessionFiles(root)

    # Update context
    context["session_files"] = session_files
    context["reactor"] = reactor

def init_logging(context):
    session_files = context["session_files"]
    
    # Setup logging
    log_filename = session_files.session_dir / "singt.log"
    logfile = open(log_filename, 'w')
    logtargets = []

    # Set up the log observer for stdout.
    logtargets.append(
        FilteringLogObserver(
            textFileLogObserver(sys.stdout),
            predicates=[LogLevelFilterPredicate(LogLevel.debug)] # was: warn
        )
    )

    # Set up the log observer for our log file. "debug" is the highest possible level.
    logtargets.append(
        FilteringLogObserver(
            textFileLogObserver(logfile),
            predicates=[LogLevelFilterPredicate(LogLevel.debug)]
        )
    )

    # Direct the Twisted Logger to log to both of our observers.
    globalLogBeginner.beginLoggingTo(logtargets)

    # ASCII-art title
    title = art.text2art("Singt Client")
    log.info("\n"+title)

def init_database(context):
    session_files = context["session_files"]
    
    # Database
    db_filename = session_files.session_dir / "database.sqlite3"
    database = Database(db_filename, context)
    context["database"] = database


def init_command(context):
    command = Command(context)
    context["command"] = command
    

def init_web_interface(context):
    web_server, eventsource_resource = create_web_interface(context)
    port = 8000
    web_server_running = None
    try:
        reactor.listenTCP(port, web_server)
        web_server_running = True
    except Exception as e:
        log.error("Web server failed:"+str(e))
        web_server_running = False
        
    if web_server_running:
        def open_browser():
            webbrowser.open("http://127.0.0.1:"+str(port))
        reactor.callWhenRunning(open_browser)

    return web_server_running


def init_gui(context, web_server_running):
    from twisted.internet import tksupport
    import tkinter as tk
    
    root = tk.Tk()
    root.resizable(False, False)
    root.title("")
    root.geometry("250x438")

    background_filenames = {
        None: "gui-background-green.gif",
        True: "gui-background-green-success.gif",
        False: "gui-background-green-failure.gif"
    }
    background_filename = pkg_resources.resource_filename(
        "singtclient",
        background_filenames[web_server_running]
    )
    background_image = tk.PhotoImage(
        file = background_filename
    )
    # A reference to the image must be kept, or we see only white
    context["gui_background_image"] = background_image
    background_label = tk.Label(root, image=background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    tksupport.install(root)

    def window_closed():
        log.info("The user closed the GUI window")
        reactor = context["reactor"]
        reactor.stop()
        
    root.protocol("WM_DELETE_WINDOW", window_closed)
    root.createcommand("::tk::mac::Quit", window_closed)

    
def init_reactor(context):
    log.info("Running reactor")
    reactor = context["reactor"]
    reactor.run()
    log.info("Finished.")


def init_headless(context):
    if "root" not in context:
        context["root"] = Path.home()
    if "udp_client_factory" not in context:
        context["udp_client_factory"] = UDPClient
    init_session(context)
    init_logging(context)
    init_database(context)
    init_command(context)
    
    
def start(context):
    init_headless(context)
    web_server_running = init_web_interface(context)
    init_gui(context, web_server_running)
    init_reactor(context)


