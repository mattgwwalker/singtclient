from singtclient import client
from singtclient import context

if __name__=="__main__":
    context = context.make_context()
    client.start(context)
    
