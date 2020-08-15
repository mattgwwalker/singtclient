from twisted.web import server
from twisted.web.static import File

from singtcommon import EventSource
from singtclient.client_web_command import CommandResource

def create_web_interface(reactor, context):
    # Load www directory
    import pkg_resources
    www_dir = pkg_resources.resource_filename('singtclient', 'www')

    # Create the web resources
    file_resource = File(www_dir)
    root = file_resource

    # Create an event source server
    eventsource_resource = EventSource()
    root.putChild(b"eventsource", eventsource_resource)

    # Create a command receiver
    command_resource = CommandResource(reactor, context)
    root.putChild(b"command", command_resource)
    
    # Create a web server
    site = server.Site(root)

    return site, eventsource_resource
