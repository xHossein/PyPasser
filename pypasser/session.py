from typing import Dict, Union
import requests
from .constants import BASE_URL, BASE_HEADERS
from .exceptions import ConnectionError


class Session():
    def __init__(self, timeout: int = 20) -> None:
        
        self.session = requests.Session()
        self.session.headers = BASE_HEADERS
        self.timeout = timeout

    def send_request(self, endpoint: str,
                     data: Union[str, Dict] = None,
                     params: str = None) -> requests.Response:
        
        try:
            if data:
                response = self.session.post(BASE_URL.format(endpoint),
                                            data=data, params=params, timeout=self.timeout)
            else:
                response = self.session.get(BASE_URL.format(endpoint),
                                            params=params, timeout=self.timeout)
                
        except requests.exceptions.RequestException:
            raise ConnectionError()
        
        except Exception as e:
            print(e)

        return response