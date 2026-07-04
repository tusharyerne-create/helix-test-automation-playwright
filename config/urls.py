from config.environment import URL

ROUTES = {
    "/login": f"{URL}/drs/",
    "/homepage": f"{URL}/drs/home",
    "/listview": f"{URL}/drs/listview",
}

def resolve(input_sheet: str) -> str | None:
    return ROUTES.get(input_sheet)
