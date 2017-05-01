import json
import logging
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from ConfigureUtil import Headers, JsonError, global_session

base_url = "http://whatson.sydney.edu.au/configuration/calendar/calendar-view2?"
base_param = {
    "SQ_CALENDAR_VIEW": "day",
    "SQ_CALENDAR_DATE": "2017-04-27"
}

headers = {
    "Host": "whatson.sydney.edu.au",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "close"
}


def new_item():
    item = {
        "title": None,
        "date": None,
        "hours": None,
        "url": None,
        "description": None
    }
    return item


class Nicholson(View):
    path = "/Museum/Nicholson"

    async def get_schedule(self):
        self.item_list = list()

        base_param["SQ_CALENDAR_DATE"] = self.request.query["date"]
        url = base_url + urlencode(base_param)
        logging.info(url)
        response = await global_session.get(url)
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        divs = soup.find_all("div")
        step = 0
        current_item = None
        for div in divs:
            if "class" in div.attrs and "event-date" in div["class"]:
                if div.text.strip() != "Date":
                    current_item = new_item()
                    current_item["date"] = div.text.strip()
                    step = 1
                    continue

            if step == 1:  # event-time
                current_item["hours"] = div.text.strip()
                step += 1
            elif step == 2:  # event-info
                h3 = div.find("h3")
                p = div.find("p")
                if h3:
                    current_item["title"] = h3.text.strip()
                    current_item["url"] = h3.find("a")["href"]
                if p:
                    current_item["description"] = p.text.strip()
                self.item_list.append(current_item)
                step = 0
            else:
                step = 0
        if not self.item_list:
            return web.Response(body=JsonError.json_param_error,
                                headers=Headers.json_headers)
        else:
            return web.Response(body=json.dumps(self.item_list),
                                headers=Headers.json_headers)

    async def get(self):
        query = self.request.query
        if "date" not in query:
            return web.Response(body=JsonError.param_error,
                                headers=Headers.json_headers)
        else:
            return await self.get_schedule()
