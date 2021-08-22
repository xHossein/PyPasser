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
## use this response in your requests ...

# for SnapChat.com
reCaptcha_response = reCaptchaBypasser(snapchat_com)
## use this response in your requests ...

```
&nbsp;
## **Option 2: Use `CustomSite` for unadded sites**
To use `CustomSite`, first you must find `endpoint` and `params` of anchor URL.
- Open inspect-element on your browser.
- Go to web page that has reCaptcha V3.
- In Network tab you should see a request with URL like this:\
 ```https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfCVLAUAAAAFwwRnnCFW_J39&co=aHR....```\
 so in this URL, **endpoint** is `api2` (it also can be `enterprise` in another sites).\
  and **params** is `ar=1&k=6LfCVLAUAAAAFwwRnnCFW_J39&co=aHR...`.


```python
from pypasser import reCaptchaBypasser
from pypasser.structs import CustomSite

config = CustomSite('endpoint', 'params')
reCaptcha_response = reCaptchaBypasser(config)
## use this response in your requests ...
```
&nbsp;
## **Use proxy**

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
         "https": "http://HOST:PORT"}

reCaptcha_response = reCaptchaBypasser(spotify_com, proxy)
```
&nbsp;
## **Set timeout**
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
RecaptchaResponseNotFound | Raised when couldn't find reCaptcha response due to using **PyPasser** for site that hasn't reCaptchaV3.
