import logging
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import httpx

from regqa.fetch.errors import DownloadError, RobotsDisallowedError

log = logging.getLogger(__name__)


class PoliteClient:
    """A single-threaded HTTP client that waits between requests.

    Serial and slow on purpose. The whole corpus is roughly a hundred files, so
    concurrency would buy a few minutes at the cost of being the noisiest thing
    in someone else's access log.
    """

    def __init__(self, user_agent: str, delay_s: float, timeout_s: float = 30.0) -> None:
        self._delay_s = delay_s
        self._last_request_at: float | None = None
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=timeout_s,
            follow_redirects=True,
        )
        self._user_agent = user_agent

    def __enter__(self) -> "PoliteClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _wait(self) -> None:
        if self._last_request_at is None:
            return
        remaining = self._delay_s - (time.monotonic() - self._last_request_at)
        if remaining > 0:
            time.sleep(remaining)

    def _robots_for(self, url: str) -> urllib.robotparser.RobotFileParser:
        origin = "{0.scheme}://{0.netloc}".format(urlparse(url))
        cached = self._robots.get(origin)
        if cached is not None:
            return cached

        parser = urllib.robotparser.RobotFileParser()
        robots_url = urljoin(origin, "/robots.txt")
        self._wait()
        response = self._client.get(robots_url)
        self._last_request_at = time.monotonic()

        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        else:
            # No robots.txt is not permission to ignore the question, but it is
            # the documented meaning of a 404: nothing is disallowed.
            parser.parse([])
        log.info("robots_loaded", extra={"url": robots_url, "status": response.status_code})

        self._robots[origin] = parser
        return parser

    def crawl_delay(self, url: str) -> float | None:
        value = self._robots_for(url).crawl_delay(self._user_agent)
        return float(value) if value is not None else None

    def get(self, url: str) -> httpx.Response:
        if not self._robots_for(url).can_fetch(self._user_agent, url):
            raise RobotsDisallowedError(f"robots.txt disallows {url}")

        self._wait()
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise DownloadError(f"request to {url} failed: {exc}") from exc
        finally:
            self._last_request_at = time.monotonic()

        if response.status_code != 200:
            raise DownloadError(f"{url} returned HTTP {response.status_code}")
        return response
