from pypasser import reCaptchaV3
import re
import requests
from requests.utils import dict_from_cookiejar

def login(email: str, password: str):
    
    # Get tokens
    response = requests.get('https://www.grammarly.com/m/signin')
    cookie = dict_from_cookiejar(response.cookies)
    csrftoken = re.findall(r'csrf-token=(.*?);',response.headers.get('Set-Cookie'))[0]
    containerId = re.findall(r'gnar_containerId=(.*?);',response.headers.get('Set-Cookie'))[0]
    
    headers ={
            'Content-Type':'application/x-www-form-urlencoded',
            'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
            'X-Container-Id':containerId,
            'X-CSRF-Token':csrftoken
    }
    response = requests.post('https://auth.grammarly.com/v3/signup/verify/email', 
                             data=f'email={email}' , headers=headers, cookies=cookie)

    # If email is valid
    if '"isValid":true' in response.text:

        headers.update({'Content-Type':'application/json'})
        response = requests.post('https://auth.grammarly.com/v3/auth/info', 
                            json={"email":email} , headers=headers, cookies=cookie)
        
        # If email exists
        if '"accountExists":true' in response.text:
            
            # Get Recaptcha Response (Bypass via PyPasser)
            recaptcha_response = reCaptchaV3(
                "https://www.google.com/recaptcha/enterprise/anchor?ar=1&k=6LdSYv0UAAAAAF5PhF0Z1rK7QiupkyRBy1ebiFc4&co=aHR0cHM6Ly93d3cuZ3JhbW1hcmx5LmNvbTo0NDM.&hl=en&v=mrdLhN7MywkJAAbzddTIjTa&size=invisible&cb=dcwmpctj4h7r"
            )
            
            # Send Login request
            payload = {
                'email_login':{
                    'email':email,
                    'password':password,
                    'secureLogin':False,
                    'captchaTokenV3': recaptcha_response
                }
            }
            response = requests.post('https://auth.grammarly.com/v3/api/login', 
                                json=payload , headers=headers, cookies=cookie).text
            
            if '"user"' in response:
                print('Logged in successfully.')

            elif 'SHOW_CAPTCHA' in response:
                print('Found reCaptcha V2. Use HQ proxy to login with reCaptchaV3, which can bypass via PyPasser.')
                
            elif '"error":"FAILURE"' in response:
                print('Wrong password.')

if __name__ == '__main__':
    login('EMAIL','PASSWORD')