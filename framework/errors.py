class StepFailure(Exception):
    def __init__(self, message: str, screenshots: list[str] | None = None):
        super().__init__(message)
        self.screenshots = screenshots or []