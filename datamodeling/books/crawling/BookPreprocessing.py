import os
import django
from django.conf import settings
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datamodeling.settings')
django.setup()

from datamodeling.books.models import Book


class BookPreprocessing:
    def __init__(self):
        self.df = pd.read_csv('./data/books.csv', encoding='utf-8')

    def preprocess(self):
        # Column Information
        print(self.df.columns)

        # Preprocessing
        self._preprocess_pubdate()
        self._preprocess_price()
        self._preprocess_page()
        self._preprocess_description()
        self._preprocess_headline()

        return self.df

    def _preprocess_pubdate(self):
        self.df['pubdate'] = self.df['pubdate'].str.replace('[^\\d ]', '')

    def _preprocess_price(self):
        self.df['price'] = self.df['price'].str.replace('[^\\d]', '')

    def _preprocess_page(self):
        self.df['page'] = self.df['page'].str.replace('[^\\d]', '')

    def _preprocess_description(self):
        self.df['description'] = self.df['description'].str.replace('\\n[\\n]+', '\\n')

    def _preprocess_headline(self):
        self.df['headline'] = self.df['headline'].str.replace('\\n[\\n]+', '\\n')


if __name__ == '__main__':
    processor = BookPreprocessing()
    processor.preprocess()