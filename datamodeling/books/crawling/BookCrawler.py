from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BookCrawler:
    def __init__(self):
        driver_path = './driver/chromedriver'
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        self.driver = webdriver.Chrome(driver_path, options=options)

    def crawl(self):
        base_url = 'http://www.kyobobook.co.kr/newproduct/newProductList.laf'
        self.driver.get(base_url)

        while True:
            self._get_item()
            next_button = self._get_next_button()
            if not next_button:
                break
            next_button.click()

        self.driver.close()

    def _get_item(self):
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        book_list_selector = '.prd_list_area .prd_list_type1 > li'
        book_list_soup = soup.select(book_list_selector)

        for book_soup in book_list_soup:
            title = book_soup.select_one('.title').text.strip()
            author = book_soup.select_one('.author').text.strip()
            publisher = book_soup.select('.publication')[0].text.strip()
            pubdate = book_soup.select('.publication')[1].text.strip()
            price = book_soup.select_one('.sell_price').text.strip()
            headline = book_soup.select_one('.info').text.strip()
            rating = book_soup.select_one('.score strong').text.strip()

            print((title, author, publisher, pubdate, price, headline, rating))

    def _get_next_button(self):
        next_button_selector = '.list_button_wrap .list_paging a.btn_next'
        next_button = self.driver.find_elements_by_css_selector(next_button_selector)
        return next_button[0] if len(next_button) else None

    def _drop_by_child(self):
        parent_handler = self.driver.current_window_handle
        self.driver.find_element_by_xpath('//*[@id="showcaseNew"]/div[4]/ul/li[1]/div/div[1]/div[2]/div[1]/a/strong').click()
        WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))

        all_handler = self.driver.window_handles
        for handler in all_handler:
            if handler != parent_handler:
                child_handler = handler

        self.driver.switch_to.window(child_handler)
        self.driver.close()

        self.driver.switch_to.window(parent_handler)
        self.driver.close()


if __name__ == '__main__':
    book_crawler = BookCrawler()
    book_crawler.crawl()
