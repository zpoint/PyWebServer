
def generate_headers(connection="close"):
    return {
        "Host": "",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko)"
                      " Chrome/19.0.1061.0 Safari/536.3",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
        "Accept-Encoding": "gzip, deflate",
        "Connection": connection
    }


def generate_cookie(cookie_dict):
    return "; ".join(("=".join((k, v)) for k, v in cookie_dict.items()))


def get_cookie_dict(resp_cookies):
    cookie_dict = dict()
    for k, v in resp_cookies.items():
        cookie_dict[k] = v.value
    return cookie_dict

