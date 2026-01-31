"""Custom exceptions for the WebSocket SSE server."""


class DuplicateConnectionError(Exception):
    """Raised when a user tries to connect with an already connected user_id."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} is already connected")


class InvalidMessageError(Exception):
    """Raised when an invalid message is received."""

    def __init__(self, message: str):
        super().__init__(message)
