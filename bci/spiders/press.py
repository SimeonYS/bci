import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import BbciItem
from itemloaders.processors import TakeFirst
import json
pattern = r'(\xa0)?'

base = 'https://www.bci.cl/saladeprensa/notas-de-prensa/media.json?per_page=8&page={}'

class PressSpider(scrapy.Spider):
    name = 'press'
    page = 1
    start_urls = [base.format(page)]
    ITEM_PIPELINES = {
        'press.pipelines.BbciPipeline': 300,

    }

    def parse(self, response):
        data = json.loads(response.text)
        for index in range(len(data['media'])):
            link = data['media'][index]['url']
            date = data['media'][index]['created_at'].split('T')[0]
            title = data['media'][index]['title']
            yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date, title=title))

        if self.page < data['meta']['total_pages']:
            self.page += 1
            yield response.follow(base.format(self.page), self.parse)

    def parse_post(self, response, date, title):
        content = response.xpath('//div[@class="description"]//text()').getall()
        content = [p.strip() for p in content if p.strip()]
        content = re.sub(pattern, "", ' '.join(content))
        if not content:
            content = "PDF file on the url"

        item = ItemLoader(item=BbciItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()