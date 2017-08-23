
def generate_headers():
    return {
        "Host": "",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0 Mozilla/5.0 (X11; "
                      "Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "close"
    }


def generate_cookie(cookie_dict):
    return "; ".join(("=".join((k, v)) for k, v in cookie_dict.items()))


def get_cookie_dict(resp_cookies):
    cookie_dict = dict()
    for k, v in resp_cookies.items():
        cookie_dict[k] = v.value
    return cookie_dict

