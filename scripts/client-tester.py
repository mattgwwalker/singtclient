from pathlib import Path
import random
import sys

from singtclient import client
from singtclient import context
from singtclient.client_udp import UDPClientTester, UDPClientRecorder


if __name__=="__main__":
    display_usage = True
    if len(sys.argv) >= 3:
        command = sys.argv[2]
        if command == "play":
            if len(sys.argv) == 4:
                display_usage = False
                filename = sys.argv[3]
        if command == "record" or command == "echo":
            if len(sys.argv) == 3:
                display_usage =	False
    
    if display_usage:
        print("Usage:")
        print("  "+sys.argv[0]+" [ip_address] play [wav_filename]")
        print("  "+sys.argv[0]+" [ip_address] record")
        print("  "+sys.argv[0]+" [ip_address] echo")
        exit()
        
    ip_address = sys.argv[1]
    
    context = context.make_context()

    random_id = random.randint(1,99999)
    context["root"] = Path.home() / "singtclient_testers" / f"{random_id:05d}"

    output_filename = str(context["root"] / "output.wav") 

    if command == "play":
        def make_udp_client(host, port, context):
            return UDPClientTester(host, port, filename, output_filename)
    else:
        echo = (command == "echo")
        def make_udp_client(host, port, context):
            return UDPClientRecorder(host, port, output_filename, echo=echo)
    context["udp_client_factory"] = make_udp_client
                
    client.init_headless(context)

    # Connect to server
    reactor = context["reactor"]
    username = f"client-{command}er-{random_id:05d}"
    def connect():
        command = context["command"]
        command.connect(username, ip_address)
    reactor.callWhenRunning(connect)
    
    # Start reactor
    client.init_reactor(context)
    
