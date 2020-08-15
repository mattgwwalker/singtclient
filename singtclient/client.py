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


def start(context):
    # Setup logging
    log_filename = Path.home() / "singt.log"
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

    # Start a logger with a namespace for a particular subsystem of our application.
    log = Logger("client")

    # ASCII-art title
    title = art.text2art("Singt")
    print(title)

    # Web Interface
    # =============

    web_server, eventsource_resource = create_web_interface(reactor, context)
    port = 8000
    web_server_running = None
    try:
        reactor.listenTCP(port, web_server)
        web_server_running = True
    except Exception as e:
        print("Web server failed:"+str(e))
        web_server_running = False
        
    if web_server_running:
        def open_browser():
            webbrowser.open("http://127.0.0.1:"+str(port))
        reactor.callWhenRunning(open_browser)


    # GUI
    # ===
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
        file=background_filename
    )
    background_label = tk.Label(root, image=background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    tksupport.install(root)

    def window_closed():
        log.info("The user closed the GUI window")
        reactor.stop()
        
    root.protocol("WM_DELETE_WINDOW", window_closed)
    root.createcommand("::tk::mac::Quit", window_closed)

    
    # Reactor
    # =======
    
    print("Running reactor")
    reactor.run()

    print("Finished.")
