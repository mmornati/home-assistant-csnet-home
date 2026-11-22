"""How the polls of CSNet Manager went: the state behind the connection sensor.

Each poll either brings the readings or fails. A failed poll keeps what went
wrong, as the API noted it for each request: no answer in time, no name
lookup, no connection, an error answer, a failed login. That tells a problem
on this side (no name lookup, often no connection) from one at CSNet (an
error answer); a timeout can be either.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .api import PROBLEM_LOGIN_REJECTED, PROBLEM_NO_DATA

# The request whose problem says the most about a failed poll comes first:
# the poll fails when the elements request does, and the login comes before it
PROBLEM_REQUEST_ORDER = ("elements", "login", "installation devices")


@dataclass
class CloudConnection:
    """What the last polls of CSNet Manager gave."""

    connected: bool | None = None
    problem: str | None = None
    failed_request: str | None = None
    detail: str | None = None
    last_success: datetime | None = None
    last_failure: datetime | None = None
    failed_polls_in_a_row: int = 0
    failed_polls_today: int = 0
    response_seconds: float | None = None
    _day: date | None = None

    def _new_day(self, now: datetime) -> None:
        """Start counting the day's failed polls again after midnight."""
        if self._day != now.date():
            self._day = now.date()
            self.failed_polls_today = 0

    def record_success(self, now: datetime, response_seconds: float | None) -> None:
        """Note a poll that brought the readings."""
        self._new_day(now)
        self.connected = True
        self.problem = self.failed_request = self.detail = None
        self.last_success = now
        self.failed_polls_in_a_row = 0
        self.response_seconds = response_seconds

    def record_failure(self, now: datetime, problems: dict[str, tuple[str, str]], rejected: bool = False) -> None:
        """Note a poll that failed, with the most telling of the problems the requests met."""
        self._new_day(now)
        self.connected = False
        self.last_failure = now
        self.failed_polls_in_a_row += 1
        self.failed_polls_today += 1
        if rejected:
            self.problem, self.failed_request, self.detail = PROBLEM_LOGIN_REJECTED, "login", None
            return
        ordered = [request for request in PROBLEM_REQUEST_ORDER if request in problems]
        ordered += [request for request in problems if request not in ordered]
        if ordered:
            request = ordered[0]
            self.problem, detail = problems[request]
            self.failed_request = request
            self.detail = detail or None
        else:
            self.problem, self.failed_request, self.detail = PROBLEM_NO_DATA, None, None

    def as_attributes(self) -> dict:
        """Return what the connection sensor shows besides its state."""
        return {
            "problem": self.problem,
            "failed_request": self.failed_request,
            "detail": self.detail,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "failed_polls_in_a_row": self.failed_polls_in_a_row,
            "failed_polls_today": self.failed_polls_today,
            "response_time": self.response_seconds,
        }
