from pathlib import Path
import random
import sys

from singtclient import client
from singtclient import context
from singtclient.client_udp import UDPClientTester


if __name__=="__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("  "+sys.argv[0]+" ip_address wav_filename")
        exit()
    ip_address = sys.argv[1]
    audio_filename = sys.argv[2]
    
    context = context.make_context()

    random_id = random.randint(1,99999)
    context["root"] = Path.home() / "singtclient_testers" / f"{random_id:05d}"

    output_filename = str(context["root"] / "output.wav") 
    def make_udp_client(host, port, context):
        return UDPClientTester(host, port, audio_filename, output_filename)
    context["udp_client_factory"] = make_udp_client
    client.init_headless(context)

    # Connect to server
    reactor = context["reactor"]
    username = f"client-tester-{random_id:05d}"
    def connect():
        print("Connecting to server with username '{username}' at address {ip_address}")
        command = context["command"]
        command.connect(username, ip_address)
    reactor.callWhenRunning(connect)
    
    # Start reactor
    client.init_reactor(context)
    
