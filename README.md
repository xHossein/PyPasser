# PyPasser
**PyPasser** is a Python library for bypassing reCaptchaV3 only by sending 2 requests. In 1st request, gets token of captcha and in 2nd request, gets `rresp` by params and token which gotted in previous step.

Support Python >= 3.7
# Installation
### From PyPI
```
pip install PyPasser
```
### From Github (latest repo code)
```
pip install git+https://github.com/xHossein/PyPasser@master
```
&nbsp;
# Usage
## **Option 1: Use the pre-added sites**
see pre-added sites [here](https://github.com/xHossein/PyPasser/blob/master/pypasser/sites.py).

```python
from pypasser import reCaptchaBypasser
from pypasser.sites import spotify_com, snapchat_com

# for Spotify.com
reCaptcha_response = reCaptchaBypasser(spotify_com)
## use this response in your request ...

# for SnapChat.com
reCaptcha_response = reCaptchaBypasser(snapchat_com)
## use this response in your request ...

```
&nbsp;
## **Option 2: Use `CustomSite` for unadded sites**
To use `CustomSite`, first you must find anchor URL.
- Open inspect-element on your browser.
- Go to the web page that has reCaptcha V3.
- In Network tab you should see many requests.
- Type `anchor` in text-field filter to hide unnecessary requests.
- Now you should see a url like this. pass it to `CustomSite`:

  >```https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfCVLAUAAAAFwwRnnCFW_J39&co=aHR....```
 
Note that the anchor urls also can have `/enterprise/anchor` instead of `/api2/anchor` in other sites.

&nbsp;
```python
from pypasser import reCaptchaBypasser
from pypasser.structs import CustomSite

config = CustomSite('ANCHOR URL')
reCaptcha_response = reCaptchaBypasser(config)
## use this response in your request ...
```
&nbsp;
## **Proxy**

```python
from pypasser import reCaptchaBypasser
from pypasser.sites import spotify_com
from pypasser.structs import Proxy

## Using Proxy structure
proxy = Proxy(Proxy.type.HTTPs,'HOST','PORT')

## with authentication credentials
# proxy = Proxy(Proxy.type.HTTPs,'HOST','PORT','USERNAME', 'PASSWORD')

reCaptcha_response = reCaptchaBypasser(spotify_com, proxy)
```
_also you can configure it as Dict._


```python

proxy = {"http": "http://HOST:PORT",
         "https": "https://HOST:PORT"}

reCaptcha_response = reCaptchaBypasser(spotify_com, proxy)
```
&nbsp;
## **Timeout**
Default timeout is `20 seconds` but you can change the amount like this:

```python
from pypasser import reCaptchaBypasser
from pypasser.sites import spotify_com

reCaptcha_response = reCaptchaBypasser(spotify_com, timeout = 10)
```
&nbsp;
# Exception
Exception | Description
----------|------------
ConnectionError | Raised due to network connectivity-related issues.
SiteNotSupported | Raised when site not in `sites.json`.
RecaptchaTokenNotFound | Raised when couldn't find token due to wrong `endpoint` or `params`.
RecaptchaResponseNotFound | Raised when couldn't find reCaptcha response due to using **PyPasser** for site that hasn't reCaptchaV3 or not vulnerable.

&nbsp;
# Legal Disclaimer
This was made for educational purposes only, nobody which directly involved in this project is responsible for any damages caused.\
**You are responsible for your actions.**

&nbsp;
# License
[MIT](https://choosealicense.com/licenses/mit/)