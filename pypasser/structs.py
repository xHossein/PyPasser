from dataclasses import dataclass
import enum
import re

@dataclass
class CustomSite:
    """
    Custom Site Structure
    ---------------
    
    Object that holds anchor url.
    
    
    Attributes
    ----------
    anchor_url: str,
        The anchor url
    
    """
    anchor_url: str
    
    def dict(self):
        regex = '(?P<endpoint>[api2|enterprise]+)\/anchor\?(?P<params>.*)'
        for match in re.finditer(regex, self.anchor_url):
            return match.groupdict()
    
class Type(enum.Enum):
    HTTPs   = 'https'
    SOCKS4 = 'socks4'
    SOCKS5 = 'socks5'
    
@dataclass
class Proxy:
    """
    Proxy Structure
    ---------------
    
    Object that holds all data about proxy.
    
    """
    type: Type = Type
    host: str = ""
    port: str = ""
    username: str = ""
    password: str = ""
    
    def dict(self):
        if self.username and self.password:
            return {'http': f'{self.type.value.replace("https","http")}://{self.username}:{self.password}@{self.host}:{self.port}',
                    'https': f'{self.type.value}://{self.username}:{self.password}@{self.host}:{self.port}'}

        return {"http": f"{self.type.value.replace('https','http')}://{self.host}:{self.port}",
                "https": f"{self.type.value}://{self.host}:{self.port}"}