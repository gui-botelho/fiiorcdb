import asyncio
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch

interest_fii_dict = {}


class FII:
    def __init__(self, code=None, sector=None, price=None, m_yield=None, vacancy=None, qt_asset=None, di_rate=None):
        self.code = code
        self.sector = sector
        self.price = price
        self.m_yield = m_yield
        self.vacancy = vacancy
        self.qt_asset = qt_asset
        self.di_rate = di_rate


    def listicle(self):
        return [self.code, self.sector, self.price, self.m_yield, self.vacancy, self.qt_asset]

    def is_good_buy(self):
        total_yield_5y = ((self.m_yield * self.price) / 100) * 60
        yield_cdi_5y = ((self.price * ((1 + ( self.di_rate/ 100)) ** 5)) - self.price) * (1 - 0.125)
        divider = '-'*53
        if total_yield_5y > yield_cdi_5y and self.qt_asset > 0:
            print(f'{divider}\n'
                  f'{self.code} is a good buy, with monthly yield of {self.m_yield} \n'
                  f'Expected yield in 5 years is: {total_yield_5y} \n'
                  f'Expected CDI yield in 5 years is: {yield_cdi_5y} \n'
                  f'Vacancy is {self.vacancy} with {self.qt_asset} assets.\n'
                  f'Current price is {self.price}.\n'
                  f'{divider}\n')


def get_fii_data():
    ranking = requests.get('https://www.fundsexplorer.com.br/ranking')

    soup = BeautifulSoup(ranking.text, features='html.parser')
    values = soup.select('.table')
    data_frame = pd.read_html(str(values), decimal=',', thousands='.')[0]

    clean_data_frame = data_frame[['Código do fundo', 'Setor', 'Preço Atual', 'DY (12M) Média',
                                   'Vacância Física', 'Quantidade Ativos']]

    clean_data_frame = clean_data_frame.fillna('0,0')
    di_rate = get_di_rate()

    for index in range(len(clean_data_frame)):
        temp_info = [clean_data_frame._get_value(index, key) for key in clean_data_frame.keys()]
        temp_info[2] = float((re.search('[0-9]*,[0-9]*', temp_info[2]).group()).replace(',', '.'))
        temp_info[3] = float((re.search('[0-9]*,[0-9]*', temp_info[3]).group()).replace(',', '.'))
        temp_info[4] = float((re.search('[0-9]*,[0-9]*', temp_info[4]).group()).replace(',', '.'))
        temp_info[5] = int(temp_info[5])
        fii = FII(temp_info[0], temp_info[1], temp_info[2], temp_info[3], temp_info[4], temp_info[5], di_rate)
        interest_fii_dict[fii.code] = fii


def get_di_rate():
    di_value = ''

    async def main():
        nonlocal di_value
        browser = await launch()
        page = await browser.newPage()
        page_path = 'https://www.b3.com.br/pt_br/'
        await page.goto(page_path)
        page_content = await page.content()
        di_soup = BeautifulSoup(page_content, 'html.parser')
        di_value = di_soup.select('.valor')[1].text
        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())
    di_value = di_value.strip('%')
    di_value = di_value.replace(',', '.')
    return float(di_value)


get_fii_data()
for code in interest_fii_dict:

    interest_fii_dict[code].is_good_buy()
