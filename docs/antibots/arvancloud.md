# ArvanCloud Interstitial

**ArvanCloud** (arvancloud.ir) is a major Iranian CDN and cloud security provider. Its anti-bot protection intercepts visitors with an interstitial JavaScript challenge page.

PyPasser clears ArvanCloud challenges in **a few seconds over pure HTTP**. It parses the challenge page, extracts the JSFuck-obfuscated mathematical equations, decodes the required cookie values directly in Python without executing JavaScript, and submits the response over HTTP.

**Zero browser, zero Node.js runtime.**

---

## Installation Requirement

ArvanCloud solving is fully contained in PyPasser's core package:

```bash
pip install PyPasser
```

---

## Quick Example (Pure HTTP)

```python
import httpx
from pypasser.antibot import arvancloud

target_url = "https://esale.ikco.ir/"

# 1. Clear the ArvanCloud challenge over pure HTTP
result = arvancloud.solve(
    url=target_url,
    timeout=30,
    attempts=3,
)

if result.is_solved:
    print("Cleared ArvanCloud challenge!")
    print("Cookies:", result.cookies)
    # Output: {'__arcsjs': '...', '__arcsjsc': '...'}

    # 2. Replay cookies over plain HTTP
    headers = {"User-Agent": result.user_agent}
    with httpx.Client(cookies=result.cookies, headers=headers) as client:
        response = client.get(target_url)
        print("Replay status:", response.status_code)
```

---

## Async Example

```python
import asyncio
import httpx
from pypasser.antibot import arvancloud

async def main():
    target_url = "https://esale.ikco.ir/"

    result = await arvancloud.asolve(target_url)

    if result.is_solved:
        async with httpx.AsyncClient(
            cookies=result.cookies,
            headers={"User-Agent": result.user_agent}
        ) as client:
            resp = await client.get(target_url)
            print("Status:", resp.status_code)

asyncio.run(main())
```

---

## API Reference

### `solve()`
```python
def solve(
    url: str,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 30,
    attempts: int = 3,
    user_agent: str = DEFAULT_UA,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    url: str,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 30,
    attempts: int = 3,
    user_agent: str = DEFAULT_UA,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | *Required* | Any protected URL on the target site. |
| `proxy` | `str \| None` | `None` | Proxy URL string (`http://`, `socks5://`). Clearance is tied to the proxy IP. |
| `timeout` | `int \| float` | `30` | Per-request HTTP timeout in seconds. |
| `attempts` | `int` | `3` | Number of challenge/response round trips before giving up. |
| `user_agent` | `str` | `DEFAULT_UA` | Browser User-Agent header sent with requests. |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when ArvanCloud sets clearance cookies.
- `cookies`: Dictionary containing `{"__arcsjs": "...", "__arcsjsc": "..."}`.
- `user_agent`: The User-Agent string used during clearance.
- `response_token`: `None`.

---

## Exceptions

| Exception | Cause |
|---|---|
| `ArvanBypassError` | Challenge could not be cleared within the attempt budget. |
| `ArvanChallengeError` | Challenge page HTML or JSFuck script could not be parsed or decoded. |
| `RequestFailed` | Network or HTTP connection error. |
