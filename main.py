#!/usr/bin/env python3
import os
import re
from multiprocessing import Pool

import requests

from pyquery import PyQuery as pq
from tqdm import trange, tqdm


def extract_books_from_url(url):
    print('Processing', url)
    r = requests.get(url)
    d = pq(r.text)
    h3 = d('h3.product-hdg a')
    result = []
    for i in h3:
        title = pq(i).text().strip()
        url = pq(i).attr('href')
        result.append({'title': title, 'url': url})
    return result


def generate_urls_by_series_page(series, max_page):
    for i in range(1, max_page + 1):
        yield 'https://bookwalker.jp/series/{}/page{}/'.format(series, i)


def extract_books_from_series(series):
    """extract book url by series_number https://bookwalker.jp/series/4206/
    :param series str/int
    :return (series_title,[{'tile':xxx,'url':xxx}])
    """
    r = requests.get('https://bookwalker.jp/series/{}/'.format(series))
    d = pq(r.text)
    series_title = (d('span.overview-hdg-txt')).text()
    print(series_title)
    if d('ul.pager-num li:last a'):
        max_page = int(d('ul.pager-num li:last a').text())
    else:
        max_page = 1
    books = []
    print('Total page number', max_page)
    for url in generate_urls_by_series_page(series, max_page):
        books.extend(extract_books_from_url(url))
    return series_title, books


def decode_cover_number(number):
    return int(str(number)[::-1]) - 1


def download_cover(folder, book):
    """
    :param folder: str folder_name
    :param book: {'title':xxx,'url':xxx}
    :return:
    """
    r = requests.get(book['url'])
    cover_number = re.search(r'<meta property="og:image" content="https://c.bookwalker.jp/(\d+)/t_700x780.jpg">',
                             r.text).group(1)
    ori_number = decode_cover_number(cover_number)
    url = 'https://c.bookwalker.jp/coverImage_{}.jpg'.format(ori_number)
    filename, ext = url.split('/')[-1].split('.')
    new_filename = '{filename} {title}.{ext}'.format(filename=filename, title=book['title'], ext=ext)
    filepath = os.path.join(folder, new_filename)
    if not os.path.exists(filepath):
        r = requests.get(url)
        with open(filepath, 'wb') as f:
            f.write(r.content)


def update():
    folders = os.listdir('./covers')
    series = []
    for folder in folders:
        if re.match(r'\d+ .+', folder):
            series.append(int(folder.split()[0]))
    series.sort()

    print(series)
    for i in series:
        download_by_series(i)


def download_by_series(series):
    """
    :param series: str/int
    """
    series_title, books = extract_books_from_series(series)
    folder = './covers/{} {}'.format(series, series_title)
    if not os.path.exists(folder):
        os.mkdir(folder)
    p = Pool(4)
    bar = trange(len(books))
    for i in books:
        p.apply_async(download_cover, [folder, i], callback=lambda x: bar.update(1))
    p.close()
    p.join()
    bar.close()


def main():
    user_input = input('Input series/update:')
    if user_input == 'update':
        update()
    else:
        for series in user_input.split(','):
            download_by_series(series)


if __name__ == '__main__':
    main()
