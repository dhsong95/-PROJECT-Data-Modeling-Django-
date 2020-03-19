import datetime
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd

import django
from django.db.utils import IntegrityError


## Python이 실행될 때 DJANGO_SETTINGS_MODULE이라는 환경 변수에 현재 프로젝트의 settings.py파일 경로를 등록합니다.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datamodeling.settings")

## 이제 장고를 가져와 장고 프로젝트를 사용할 수 있도록 환경을 만듭니다.
django.setup()

from books.models import Book, Author, Publisher

class BookCrawler:
    def __init__(self):
        driver_path = './driver/chromedriver'
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        self.driver = webdriver.Chrome(driver_path, options=options)
        self.df_books = pd.DataFrame()

    def crawl(self):
        base_url = 'http://www.kyobobook.co.kr/newproduct/newProductList.laf'
        self.driver.get(base_url)

        num_page = 1
        while True:
            print('Start Page No. {:02d}'.format(num_page))
            self._get_item()
            num_page += 1
            next_button = self._get_next_button()
            if not next_button:
                break
            self.driver.execute_script('arguments[0].click();', next_button)
        self.driver.close()

        datetime.datetime.now()

        self.df_books.to_csv('./data/books_{}.csv'.format(datetime.datetime.now()), encoding='utf-8', index=False)

    def _get_item(self):
        books = []
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        book_list_selector = '.prd_list_area .prd_list_type1 > li'
        book_list_soup = soup.select(book_list_selector)

        for idx, book_soup in enumerate(book_list_soup):
            title = book_soup.select_one('.title').text.strip()
            author = book_soup.select_one('.author').text.strip()
            publisher = book_soup.select('.publication')[0].text.strip()
            pubdate = book_soup.select('.publication')[1].text.strip()
            price = book_soup.select_one('.sell_price').text.strip()
            headline = book_soup.select_one('.info').text.strip()
            rating = book_soup.select_one('.score strong').text.strip()

            row = (title, author, publisher, pubdate, price, headline, rating)

            link_selector = '.prd_list_area ul.prd_list_type1 > li:nth-child({:}) .title a'.format(str(6 * (idx + 1)))
            row += (self._to_item_page(link_selector))
            books.append(row)

            if idx % 5 == 0:
                print('\tbook data of index {:02d}'.format(idx))

        self.df_books = self.df_books.append(pd.DataFrame(books, columns=['title', 'author', 'publisher', 'pubdate', 'price', 'headline', 'rating', 'isbn_13', 'isbn_10', 'page', 'description']))
        self.df_books.reset_index(drop=True, inplace=True)

    def _get_next_button(self):
        next_button_selector = '.list_button_wrap .list_paging a.btn_next'
        next_button = self.driver.find_elements_by_css_selector(next_button_selector)
        return next_button[0] if len(next_button) else None

    def _to_item_page(self, selector):
        parent_handler = self.driver.current_window_handle
        self.driver.find_element_by_css_selector(selector).click()
        try:
            WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))
        except TimeoutException:
            self.driver.switch_to.alert.accept()
            self.driver.back()
            return '', '', '', ''

        all_handler = self.driver.window_handles
        for handler in all_handler:
            if handler != parent_handler:
                child_handler = handler

        self.driver.switch_to.window(child_handler)

        item_page = self.driver.page_source
        item_soup = BeautifulSoup(item_page, 'html.parser')
        isbn_13 = isbn_10 = ''
        isbn_list = item_soup.select('.box_detail_content .table_simple2.table_opened tbody tr:nth-child(1) td span')
        for isbn in isbn_list:
            isbn = isbn.text.strip()
            if len(isbn) == 13:
                isbn_13 = isbn
            elif len(isbn) == 10:
                isbn_10 = isbn
        page = item_soup.select_one('.box_detail_content .table_simple2.table_opened tbody tr:nth-child(2) td').text.strip()
        description = item_soup.select_one('.box_detail_article').text.strip()
        self.driver.close()
        self.driver.switch_to.window(parent_handler)
        return isbn_13, isbn_10, page, description

    def _preprocess(self):
        # Column Information
        # print(self.df_books.columns)

        # Pre-Processing
        self._preprocess_pubdate()
        self._preprocess_price()
        self._preprocess_page()
        self._preprocess_description()
        self._preprocess_headline()

    def _preprocess_pubdate(self):
        self.df_books['pubdate'] = self.df_books['pubdate'].str.replace('[^\\d ]', '')

    def _preprocess_price(self):
        self.df_books['price'] = self.df_books['price'].str.replace('[^\\d]', '')

    def _preprocess_page(self):
        self.df_books['page'] = self.df_books['page'].str.replace('[^\\d]', '')

    def _preprocess_description(self):
        self.df_books['description'] = self.df_books['description'].str.replace('\\n[\\n]+', '\\n')

    def _preprocess_headline(self):
        self.df_books['headline'] = self.df_books['headline'].str.replace('\\n[\\n]+', '\\n')

    def save_to_model(self):
        self._integrate_data()
        self._preprocess()

        self._save_publisher()
        self._save_author()
        self._save_book()

    def _integrate_data(self):
        data_dir = './data'
        self.df_books = pd.DataFrame()
        for filename in os.listdir(data_dir):
            filename = os.path.join(data_dir, filename)
            sub_df = pd.read_csv(filename, encoding='utf-8')
            self.df_books = self.df_books.append(pd.DataFrame(sub_df, columns=['title', 'author', 'publisher', 'pubdate',
                                                                              'price', 'headline', 'rating', 'isbn_13',
                                                                              'isbn_10', 'page', 'description']))
            self.df_books.reset_index(drop=True, inplace=True)

    def _save_publisher(self):
        print('... Save Model Publisher ...')
        publishers = self.df_books['publisher']
        for p in publishers:
            publisher = Publisher(name=p)
            try:
                publisher.save()
            except IntegrityError:
                pass

    def _save_author(self):
        print('... Save Model Author ...')
        authors = self.df_books['author']
        for a in authors:
            author = Author(name=a)
            try:
                author.save()
            except IntegrityError:
                pass

    def _save_book(self):
        print('... Save Model Book ...')
        for _, row in self.df_books.iterrows():
            price = int(row['price'])
            pub_date_list = row['pubdate'].split()
            pub_date = datetime.datetime(int(pub_date_list[0]), int(pub_date_list[1]), int(pub_date_list[2]))
            try:
                page = int(row['page'])
            except ValueError:
                page = None
            rating = float(row['rating'])
            publisher = Publisher.objects.get(name=row['publisher'])
            book = Book(isbn_13=row['isbn_13'], isbn_10=row['isbn_10'], title=row['title'], price=price, pub_date=pub_date, page=page, headline=row['headline'], description=row['description'], rating=rating, publisher=publisher)
            try:
                book.save()
            except IntegrityError:
                book = Book.objects.get(title=row['title'])

            author = Author.objects.get(name=row['author'])
            book.authors.add(author)
            book.save()


if __name__ == '__main__':
    book_crawler = BookCrawler()
    # book_crawler.crawl()
    # book_crawler.preprocess()
    book_crawler.save_to_model()
