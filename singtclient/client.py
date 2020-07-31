import copy
from pathlib import Path
import random
import sys
import threading
import webbrowser

import art
import numpy
import sounddevice as sd
from twisted.internet import reactor
from twisted.logger import Logger, LogLevel, LogLevelFilterPredicate, \
    textFileLogObserver, FilteringLogObserver, globalLogBeginner

from singtclient.client_web import create_web_interface


def start():
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



    title = art.text2art("Singt")
    print(title)

    # Web Interface
    # =============

    web_server, eventsource_resource = create_web_interface(reactor)
    port = 8000
    reactor.listenTCP(port, web_server)

    def open_browser():
        webbrowser.open("http://127.0.0.1:"+str(port))
    reactor.callWhenRunning(open_browser)
    
    # Reactor
    # =======
    
    print("Running reactor")
    reactor.run()

    print("Finished.")



if __name__=="__main__":
    # # Ensure the user has called this script with the correct number
    # # of arguments.
    # if len(sys.argv) != 3:
    #     print("Usage:")
    #     print(f"   {sys.argv[0]} ip-address name")
    #     exit()

    # # Extract values for the IP address and the user's name
    # address = sys.argv[1]
    # username = sys.argv[2]

    start()#address, username)
    
