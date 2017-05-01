import json
import hashlib
from urllib.parse import urlencode
from aiohttp import web
from aiohttp.web import View
from ConfigureUtil import Headers, JsonError, global_session


class ESProxy(View):
    path = "/Proxy"

    def pre_check_param(self):
        query = self.request.query
        headers = self.request.headers

        if "index" not in query or "platform" not in query or "sign" not in query \
                or "apikey" not in headers or "real_host" not in headers or "api_host" not in headers:
            return web.Response(body=JsonError.json_param_error, headers=Headers.json_headers)

        sign = hashlib.md5((query["index"] + query["platform"] +
                            headers["apikey"] + headers["real_host"]).encode("utf8")).hexdigest()
        if sign != query["sign"]:
            return web.Response(body=JsonError.json_request_illegal, headers=Headers.json_headers)

    def get_url_and_headers(self):
        base_url = "http://" + self.request.headers["real_host"] + "/" + self.request.query["index"] + \
                   "/" + self.request.query["platform"] + "/_search?"

        headers = {
            "Host": self.request.headers["api_host"],
            "apikey": self.request.headers["apikey"]
        }
        return base_url, headers

    async def search_till_end(self, base_url, headers, body=None, size=10000, from_=0, ret_list=None):
        if not ret_list:
            ret_list = []
        if not body:
            body = {
                "size": size,
                "query": {"match_all": {}}
            }
        url = base_url + "from=" + str(from_)
        print(url)
        async with global_session.get(url, data=body, headers=headers) as response:
            result = await response.text()
            print(result)
            result = json.loads(result)
        if "error" in result:
            return web.Response(body=json.dumps(result), headers=Headers.json_headers)
        result_list = [hit["_source"] for hit in result['hits']['hits']]
        # print(result)
        ret_list.extend(result_list)
        if len(ret_list) < result['hits']['total']:
            return await self.search_till_end(base_url, headers, body, size, from_+size, ret_list)
        else:
            return web.Response(body=json.dumps(result_list), headers=Headers.json_headers)

    async def get(self):
        check_fail = self.pre_check_param()
        if check_fail:
            return check_fail

        url, headers = self.get_url_and_headers()
        return await self.search_till_end(url, headers)
