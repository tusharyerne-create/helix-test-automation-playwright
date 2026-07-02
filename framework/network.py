
from playwright.sync_api import Page, Response


class NetworkCapture:
    def __init__(self, page: Page):
        self._responses: list[dict] = []
        page.on("response", self._on_response)

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

    def clear(self) -> None:
        self._responses.clear()
