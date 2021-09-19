import re

def parse_url(anchor_url: str) -> dict:
    regex = '(?P<endpoint>[api2|enterprise]+)\/anchor\?(?P<params>.*)'
    for match in re.finditer(regex, anchor_url):
        return match.groupdict()
    
def proxy_dict(type, host, port, username, password):
    if username and password:
        return {'http': f'{type.value.replace("https","http")}://{username}:{password}@{host}:{port}',
                'https': f'{type.value}://{username}:{password}@{host}:{port}'}

    return {"http": f"{type.value.replace('https','http')}://{host}:{port}",
            "https": f"{type.value}://{host}:{port}"}
