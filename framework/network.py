from playwright.sync_api import Page, Response


class NetworkCapture:
    # The one NetworkCapture created per run (see runner.py) registers
    # itself here on construction. This is what lets framework/report.py
    # pull "the status code of whatever just happened" automatically,
    # without every page module having to accept/pass a NetworkCapture
    # instance around or call clear()/get_latest() itself.
    _active: "NetworkCapture | None" = None

    def __init__(self, page: Page):
        self._responses: list[dict] = []
        page.on("response", self._on_response)
        NetworkCapture._active = self

    def _on_response(self, response: Response) -> None:
        try:
            if response.request.resource_type not in ("xhr", "fetch", "document"):
                return
            self._responses.append({
                "url": response.url,
                "status": response.status,
                "body": response.text() if response.ok or response.status != 0 else "",
            })
        except Exception:
            pass

    def get_api_response(self, url_fragment: str) -> dict | None:
        matches = [r for r in self._responses if url_fragment in r["url"]]
        return matches[-1] if matches else None

    def get_last_error_response(self) -> dict | None:
        errors = [r for r in self._responses if r["status"] not in range(200, 300) and r["status"] != 0]
        return errors[-1] if errors else None

    def get_latest(self) -> dict | None:
        """The most recently captured request/response — whatever actually
        fired for the action that just happened."""
        return self._responses[-1] if self._responses else None

    def clear(self) -> None:
        self._responses.clear()


def get_active_capture() -> "NetworkCapture | None":
    """Returns this run's NetworkCapture instance, if one exists yet.
    framework/report.py calls this to auto-fill 'Http Status' for any
    sheet that has that column — no page module needs to know this exists."""
    return NetworkCapture._active

