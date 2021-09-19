# PyPasser
**PyPasser** is a Python library for bypassing reCaptchaV3 only by sending HTTP requests.

🔴 This bypass does not work on all sites. Test on your target to find out.

Support Python >= 3.7

&nbsp;

**To Do**:
- [ ] Bypass reCaptchaV2 (Selenium)
- [ ] Add more speech-to-text engine
- [ ] Calculate success rate on each engine (README.md)

&nbsp;
# Installation
### Install from PyPI
```
pip install PyPasser
```
### And for update
```
pip install PyPasser --upgrade
```

&nbsp;
### Install from Github (latest repo code)
```
pip install git+https://github.com/xHossein/PyPasser@master
```
&nbsp;
# **Usage**

## Bypass **reCaptchaV3**


To bypass recaptcha v3, first you must find anchor URL.
- Open inspect-element on your browser.
- Go to the web page that has reCaptcha V3 (not V2 invisible).
- In Network tab you should see many requests.
- Type `anchor` in text-field filter to hide unnecessary requests.
- Now you should see a url like this:

  >```https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfCVLAUAAAAFwwRnnCFW_J39&co=aHR....```

  pass this url to `reCaptchaV3` class:
 
Note that the anchor urls also can have `/enterprise/anchor` instead of `/api2/anchor` in other sites.

&nbsp;
```python
from pypasser import reCaptchaV3

reCaptcha_response = reCaptchaV3('ANCHOR URL')
## use this response in your request ...
```
Some good examples are [here](https://github.com/xHossein/PyPasser/tree/master/examples/reCaptchaV3).

&nbsp;
## **Proxy**

```python
from pypasser import reCaptchaV3
from pypasser.structs import Proxy

## Using Proxy structure
proxy = Proxy(Proxy.type.HTTPs,'HOST','PORT')

## with authentication credentials
# proxy = Proxy(Proxy.type.HTTPs,'HOST','PORT','USERNAME', 'PASSWORD')

reCaptcha_response = reCaptchaV3('ANCHOR URL', proxy)
```
_also you can configure it as Dict._


```python

proxy = {"http": "http://HOST:PORT",
         "https": "https://HOST:PORT"}

reCaptcha_response = reCaptchaV3(spotify_com, proxy)
```
&nbsp;
## **Timeout**
Default timeout is `20 seconds` but you can change the amount like this:

```python
from pypasser import reCaptchaV3

reCaptcha_response = reCaptchaV3('ANCHOR URL', timeout = 10)
```
&nbsp;
# Exception
Exception | Description
----------|------------
ConnectionError | Raised due to network connectivity-related issues.
RecaptchaTokenNotFound | Raised when couldn't find token due to wrong `anchor_url`.
RecaptchaResponseNotFound | Raised when couldn't find reCaptcha response due to using **PyPasser** for site that hasn't reCaptchaV3.

&nbsp;
# Legal Disclaimer
This was made for educational purposes only, nobody which directly involved in this project is responsible for any damages caused.\
**You are responsible for your actions.**

&nbsp;
# License
[MIT](https://choosealicense.com/licenses/mit/)
