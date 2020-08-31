class SessionFiles:
    def __init__(self, root_dir):
        # Define directories
        self.session_dir = root_dir / "singtclient_session_files"

        # Ensure directories exist
        self.session_dir.mkdir(exist_ok=True, parents=True)

    def get_path_audio_id(self, audio_id):
        return self.session_dir / f"{audio_id}.opus"
