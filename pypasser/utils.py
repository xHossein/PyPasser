import json
import pathlib
from .exceptions import SiteNotSupported

FILE_PATH = pathlib.Path(__file__).parent.joinpath('sites.json')
JSON_DATA = json.loads(open(FILE_PATH).read())

def extractor(site: str) -> dict:
    if site in JSON_DATA:    
        return JSON_DATA[site]
    
    raise SiteNotSupported(site)
