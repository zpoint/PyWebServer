def generate_cookie(cookie_dict):
    return ";".join(("=".join((k, v)) for k, v in cookie_dict.items()))


def get_cookie_dict(resp_cookies):
    cookie_dict = dict()
    for k, v in resp_cookies.items():
        cookie_dict[k] = v.value
    return cookie_dict

