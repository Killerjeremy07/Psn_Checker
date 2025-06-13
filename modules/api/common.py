class APIError(Exception):
    "Exception raised for any type of errors in the API."
    def __init__(self, message: str) -> None:
        self.message = message