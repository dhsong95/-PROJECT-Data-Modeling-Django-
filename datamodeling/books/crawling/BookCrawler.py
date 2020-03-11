from bs4 import BeautifulSoup
from selenium import webdriver
import time


class BookCrawler:
    def __init__(self):
        driver_path = './driver/chromedriver'
        self.driver = webdriver.Chrome(driver_path)

    def crawl(self, num_pages):
        books = []
        base_url = 'https://www.aladin.co.kr/shop/common/wnew.aspx?NewType=SpecialNew&BranchType=1&CID=1'
        for page in range(num_pages):
            url = base_url + '&page=' + str(page)
            books += (self._get_book_list(url))

        for (title, url) in books:
            self.driver.get(url)
            self.driver.find_element_by_class_name('pContent').is_displayed()

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            information = soup.select('.Ere_prod_mconts_box')
            for info in information:
                print(info.select_one('.Ere_prod_mconts_LS').text.strip())

        self.driver.close()

    def _get_book_list(self, url):
        book_list = []
        self.driver.get(url)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        books = soup.select('#Myform .ss_book_box')
        for book in books:
            title_soup = book.select_one('.ss_book_list:nth-child(1) li a.bo3')
            title = title_soup.text.strip()
            book_url = title_soup['href']
            book_list.append((title, book_url))
        return book_list


if __name__ == '__main__':
    book_crawler = BookCrawler()
    book_crawler.crawl(10)
