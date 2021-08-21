class RecaptchaTokenNotFound(Exception):
    def __init__(self):
        super().__init__('Recaptcha token not found.')

class RecaptchaResponseNotFound(Exception):
    def __init__(self):
        super().__init__('Recaptcha response not found.')
        
        
class SiteNotSupported(Exception):
    def __init__(self, *args):
        super().__init__('This site is not in supported list.', *args)
        
        
class ConnectionError(Exception):
    pass