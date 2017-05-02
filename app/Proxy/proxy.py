import json
import hashlib
import logging
import asyncio
from aiohttp import web
from aiohttp.web import View
from ConfigureUtil import Headers, JsonError, global_session


class ESProxy(View):
    path = "/ESProxy"

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
        self.ret_index_and_doc = list()
        ret_urls = list()
        ret_headers = list()
        base_url = "http://" + self.request.headers["real_host"] + "/%s/%s/_search?"
        headers = {
            "Host": self.request.headers["api_host"],
            "apikey": self.request.headers["apikey"]
        }
        for index, doc_type in zip(self.request.query["index"].split(","), self.request.query["platform"].split(",")):
            ret_urls.append(base_url % (index, doc_type))
            ret_headers.append(headers)
            self.ret_index_and_doc.append((index, doc_type))
        return ret_urls, ret_headers

    async def search_till_end(self, base_url, headers, body=None, size=10000, from_=0, ret_list=None):
        if not ret_list:
            ret_list = []
        if not body:
            body = {
                "size": size,
                "query": {"match_all": {}}
            }
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        url = base_url + "from=" + str(from_)
        logging.info(url)
        async with global_session.get(url, data=body, headers=headers) as response:
            result = await response.text()
            result = json.loads(result)
        if "error" in result:
            return result
        result_list = [hit["_source"] for hit in result['hits']['hits']]
        # print(result)
        ret_list.extend(result_list)
        if len(ret_list) < result['hits']['total']:
            return await self.search_till_end(base_url, headers, body, size, from_+size, ret_list)
        else:
            return result_list

    async def get_and_wait_all_tasks(self, urls, headers):
        result_dict = dict()
        tasks = [self.search_till_end(url, header) for url, header in zip(urls, headers)]
        responses = await asyncio.gather(*tasks)
        for index_and_doc, response in zip(self.ret_index_and_doc, responses):
            result_dict[",".join(index_and_doc)] = response
        return web.Response(body=json.dumps(result_dict), headers=Headers.json_headers)

    async def get(self):
        check_fail = self.pre_check_param()
        if check_fail:
            return check_fail

        urls, headers = self.get_url_and_headers()
        return await self.get_and_wait_all_tasks(urls, headers)
