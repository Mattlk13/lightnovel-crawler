# -*- coding: utf-8 -*-
import re
import logging
from urllib.parse import quote_plus

from lncrawl.core.crawler import Crawler

logger = logging.getLogger(__name__)
search_url = 'https://noveltoon.mobi/en/search?word=%s&source=&lock='


class NovelsRockCrawler(Crawler):
    base_url = 'https://noveltoon.mobi/'

    def search_novel(self, query):
        query = quote_plus(query.lower())
        soup = self.get_soup(search_url % query)

        results = []
        for a in soup.select('.search-main a')[:10]:
            results.append({
                'url': self.absolute_url(a['href']),
                'title': a.select_one('.search-item-title').text.strip(),
                'info': ', '.join([
                    e.text.strip() for e in a.select('.search-label-text')
                    if e and e.text.strip()
                ]),
            })
        # end for

        return results
    # end def

    def read_novel_info(self):
        self.novel_url = re.sub(r'/detail/(\d+)(/\w+)?',
                                lambda m: '/detail/%s/episodes' % m.group(1), self.novel_url)

        logger.debug('Visiting %s', self.novel_url)
        soup = self.get_soup(self.novel_url)

        self.novel_title = soup.select_one('.detail-top .detail-title').text.strip()
        logger.info('Novel title: %s', self.novel_title)

        try:
            self.novel_cover = self.absolute_url(
                soup.select_one('.detail-top .detail-top-right img')['src'])
        except Exception as e:
            logger.debug('Failed to get novel cover', e)
        logger.info('Novel cover: %s', self.novel_cover)

        try:
            self.novel_author = soup.select_one('.detail-top .detail-author').text.strip()
        except Exception as e:
            logger.debug('Failed to get novel author', e)
        logger.info('Novel author: %s', self.novel_author)

        for a in soup.select('a.episodes-info-a-item'):
            chap_id = len(self.chapters) + 1
            vol_id = chap_id // 100 + 1
            if chap_id % 100 == 1:
                self.volumes.append({'id': vol_id})
            # end if
            self.chapters.append({
                'id': chap_id,
                'volume': vol_id,
                'url':  self.absolute_url(a['href']),
                'title': a.select_one('.episode-item-title').text.strip(),
            })
        # end for
    # end def

    def download_chapter_body(self, chapter):
        logger.info('Downloading %s', chapter['url'])
        soup = self.get_soup(chapter['url'])
        contents = soup.select_one('.watch-chapter-detail')
        self.blacklist_patterns = [
            r"Don't forget to leave a like and subscribe to this new novel.",
            r"Feel free to comment your thoughts below.",
            r'——————————————————.*',
            r"Don't forget to leave like sub to this new novel.",
            r'Feel free to comment below.',
        ]
        return self.extract_contents(contents)
    # end def
# end class
