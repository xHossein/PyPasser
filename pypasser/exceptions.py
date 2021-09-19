class RecaptchaTokenNotFound(Exception):
    def __init__(self):
        super().__init__('Recaptcha token not found.')

class RecaptchaResponseNotFound(Exception):
    def __init__(self):
        super().__init__('Recaptcha response not found.')
        
class ConnectionError(Exception):
    pass