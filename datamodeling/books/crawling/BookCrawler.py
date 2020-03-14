from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


class BookCrawler:
    def __init__(self):
        driver_path = './driver/chromedriver'
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        self.driver = webdriver.Chrome(driver_path, options=options)
        self.df = pd.DataFrame()

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
        self.df.to_csv('./data/books.csv', encoding='utf-8', index=False)

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

        self.df = self.df.append(pd.DataFrame(books, columns=['title', 'author', 'publisher', 'pubdate', 'price', 'headline', 'rating', 'isbn_13', 'isbn_10', 'page', 'description']))
        self.df.reset_index(drop=True, inplace=True)

    def _get_next_button(self):
        next_button_selector = '.list_button_wrap .list_paging a.btn_next'
        next_button = self.driver.find_elements_by_css_selector(next_button_selector)
        return next_button[0] if len(next_button) else None

    def _to_item_page(self, selector):
        parent_handler = self.driver.current_window_handle
        self.driver.find_element_by_css_selector(selector).click()
        WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))

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


if __name__ == '__main__':
    book_crawler = BookCrawler()
    book_crawler.crawl()
