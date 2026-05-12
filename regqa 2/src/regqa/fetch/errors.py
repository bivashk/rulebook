class FetchError(RuntimeError):
    """Base for everything this package raises."""


class RobotsDisallowedError(FetchError):
    """The site's robots.txt forbids the URL we were about to request."""


class ParseError(FetchError):
    """A listing page did not have the structure the parser expects."""


class DownloadError(FetchError):
    """A document could not be retrieved."""
