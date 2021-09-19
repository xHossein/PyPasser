from pypasser import reCaptchaV3
import re
import requests

def login(email: str, password: str):
    base_headers = {
                'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
                'x-requested-with':'XMLHttpRequest',
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                'referer':'https://maktabkhooneh.org/',
        }
    
    # Get CSRF tokens
    response = requests.get('https://maktabkhooneh.org/', headers = base_headers)
    csrftoken = re.findall(r'csrftoken=(.*?);',response.headers.get('Set-Cookie'))[0]
    csrfmiddlewaretoken = re.findall(r'name="csrfmiddlewaretoken" value="(.*?)"',response.text)[0]

    # Get Recaptcha Response (Bypass via PyPasser)
    recaptcha_response = reCaptchaV3(
        "https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LcE-NAZAAAAANzz4-ai_pMkuXnpCXFJ6zqsQIHf&co=aHR0cHM6Ly9tYWt0YWJraG9vbmVoLm9yZzo0NDM.&hl=fa&v=mrdLhN7MywkJAAbzddTIjTaM&size=invisible&sa=login&cb=5wc9ld72y29u"
        )
    
    # Send Login request
    payload = {
        'csrfmiddlewaretoken': csrfmiddlewaretoken,
        'tessera': email,
        'g-recaptcha-response': recaptcha_response,
        'csrfmiddlewaretoken': csrfmiddlewaretoken,
        'hidden_username': email,
        'password': password
    }
    base_headers.update({'cookie':f'csrftoken={csrftoken};'})
    response = requests.post('https://maktabkhooneh.org/auth/login-authentication', data=payload, headers=base_headers).json()
    
    if response['message'] == "logined":
        print('Logged in successfully.')
    
    elif response['message'] == "password":
        print('Wrong password.')



if __name__ == '__main__':
    login('EMAIL','PASSWORD')