class SessionFiles:
    def __init__(self, root_dir):
        # Define directories
        self.session_dir = root_dir / "singtclient_session_files"

        # Ensure directories exist
        self.session_dir.mkdir(exist_ok=True, parents=True)
