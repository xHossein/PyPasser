from dataclasses import dataclass
import enum

@dataclass
class CustomSite:
    """
    Custom Site Structure
    ---------------
    
    Object that holds endpoint and params.
    
    
    Attributes
    ----------
    endpoint: str,
        check `anchor URL`, it should be `api2` or `enterprise`.
    
    params: str,
        params of `anchor URL`.
    
    """
    endpoint: str
    params: str

    def dict(self):
        return vars(self)
    
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