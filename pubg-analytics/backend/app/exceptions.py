class PUBGClientError(Exception):
    """Base exception for upstream PUBG API failures."""


class PlayerNotFoundError(PUBGClientError):
    pass


class RateLimitedError(PUBGClientError):
    pass


class PUBGAPIUnavailableError(PUBGClientError):
    pass


class PUBGAPIError(PUBGClientError):
    pass


class InvalidPUBGDataError(PUBGClientError):
    pass
