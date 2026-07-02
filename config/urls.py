"""
urls.py
Owns: mapping a Scenario sheet's InputSheet value (e.g. "/login") to a real
navigable URL, when a step actually needs a route instead of a menu click.
Never put a literal URL inside a module.
"""
from config.environment import URL

ROUTES = {
    "/login": f"{URL}/drs/",
    "/homepage": f"{URL}/drs/home",
    "/listview": f"{URL}/drs/listview",
}


def resolve(input_sheet: str) -> str | None:
    """Returns a full URL for a route-style InputSheet value, or None if
    the InputSheet is actually a menu/search term (e.g. 'List View') rather
    than a route."""
    return ROUTES.get(input_sheet)
