import json
import hashlib
import logging
import asyncio
import datetime
from aiohttp import web
from aiohttp.web import View
from ConfigureUtil import Headers, JsonError, global_session

prev_result = None
prev_datetime = None
handling = False


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
        return json.dumps(result_dict)

    async def get_tasks_and_fetch(self):
        global handling, prev_result, prev_datetime
        handling = True
        urls, headers = self.get_url_and_headers()
        prev_result = await self.get_and_wait_all_tasks(urls, headers)
        prev_datetime = datetime.datetime.now()
        handling = False
        return web.Response(body=prev_result, headers=Headers.json_headers)

    async def wait_for_handling(self):
        global handling, prev_result
        while handling:
            await asyncio.sleep(0.5)
        return web.Response(body=prev_result, headers=Headers.json_headers)

    async def do_get(self):
        global prev_result, prev_datetime, handling
        if not prev_datetime:
            prev_datetime = datetime.datetime.now()
            return await self.get_tasks_and_fetch()

        date_now = datetime.datetime.now()
        if (date_now - prev_datetime).days > 1:
            if handling:
                return await self.wait_for_handling()
            else:
                return await self.get_tasks_and_fetch()
        else:
            return await self.get_tasks_and_fetch()
            # return web.Response(body=prev_result, headers=Headers.json_headers)

    async def get(self):
        check_fail = self.pre_check_param()
        if check_fail:
            return check_fail

        return await self.do_get()
