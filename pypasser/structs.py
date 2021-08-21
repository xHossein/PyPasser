from dataclasses import dataclass

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