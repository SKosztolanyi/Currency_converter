#!/usr/bin/env python3
"""
Created on Sat Aug 12 16:18:30 2017

@author: pista
"""

# imports
import os
import io
import datetime
import string
import json
import argparse
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

# class definitnions
class ConvertMoney(object):
    """A customer of ABC Bank with a checking account. Customers have the
    following properties:

    Attributes:
        amount: A float tracking the amount of money.
        currency: A string code or symbol of currency.
    """

    def __init__(self, amount=0.0, in_curr_symbol='CZK', out_curr_symbol=None):
        """dafd
        fdafdas."""
        self.amount = amount
        self.in_curr_symbol = in_curr_symbol
        self.out_curr_symbol = out_curr_symbol
    
    def get_current_rates(self, rates_table):
        
        available_currencies = sorted(list(rates_table.loc[:,'code']))
        try:
            bad_symbol = self.in_curr_symbol
            rates_table['code'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
            bad_symbol = self.out_curr_symbol
            if self.out_curr_symbol != 'ALL':
                rates_table['code'][(rates_table['code'] == self.out_curr_symbol) |
                        (rates_table['symbol'] == self.out_curr_symbol)].values[0]  
        except:
            print(bad_symbol, ''' is not in this currency table.
            Use one of the available currencies: '''), 
            print(available_currencies)
            raise SystemExit
            
        self.input_currency = rates_table['code'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
        self.output_currency = rates_table['code'][(rates_table['code'] == self.out_curr_symbol) |
                                        (rates_table['symbol'] == self.out_curr_symbol)].values
        self.input_rate = rates_table['rate'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
        self.output_rate = rates_table['rate'][(rates_table['code'] == self.out_curr_symbol) |
                                        (rates_table['symbol'] == self.out_curr_symbol)].values
        self.input_index = rates_table['amount_index'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
        self.output_index = rates_table['amount_index'][(rates_table['code'] == self.out_curr_symbol) |
                                        (rates_table['symbol'] == self.out_curr_symbol)].values

        rates_table['CZK_amount'] = self.amount/self.input_index*self.input_rate
        rates_table['converted_amount'] = (rates_table['CZK_amount']*rates_table['amount_index']/
                                          rates_table['rate']).round(2)
        self.output_table = rates_table.loc[:,['code', 'converted_amount']]
                     
    def convert_currency(self):
        full_json = {}
        full_json['input'] = {}
        full_json['input']['amount'] = self.amount
        full_json['input']['currency'] = self.input_currency # change for 3 code letter from table
        full_json['output'] = {}
        # iterate over row of df and add to output - need to do with rate and index as well
        if self.out_curr_symbol == 'ALL':
            full_json['output'] = dict(zip(self.output_table.code,
                                           self.output_table.converted_amount))
        else:
            output_amount = self.output_table['converted_amount'][
                self.output_table['code'] == self.output_currency[0]].values[0]
            full_json['output'][self.output_currency[0]] = output_amount
        return full_json


# function definitions
def create_directories(*args):
    for dir in args:
        if not os.path.exists(dir):
            os.makedirs(dir)

def create_cnb_date(string_date):
    """ Returns today's date in correct format for CNB current Exchange Rates.
    If no date is specified, today's date is used.
    """
    if not isinstance(string_date, str):
        raise TypeError('input variable is not a string')
    if string_date != 'now':
        # remove punctuation from string
        translator = str.maketrans('', '', string.punctuation)
        cnb_date = string_date.translate(translator)
    else:
        current_date = datetime.date.today()
        current_time = int(datetime.datetime.today().strftime('%H%M'))
        week_day = datetime.date.today().weekday()
    if current_time < 1430:
        week_day = datetime.date.today().weekday() - 1     
    if week_day in [5, 6]:
        current_date = (current_date - datetime.timedelta(days=6%week_day))
    cnb_date = current_date.strftime('%Y-%m-%d')
    return cnb_date

def download_cnb_rates(string_date='now'):
    """
    docs go here
    """
    cnb_date = create_cnb_date(string_date)
    year = cnb_date[0:4]
    month = cnb_date[5:7]
    day = cnb_date[8:10]
    full_date = '.'.join([day, month, year])
    url_body = 'https://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.txt?date='
    full_url = ''.join([url_body, full_date])
    r = requests.get(full_url)
    try:
        r.status_code == 200
    except requests.exceptions.HTTPError as err:
        print(err)
    request_date = '-'.join([r.content.decode('utf-8')[6:10],
                             r.content.decode('utf-8')[3:5],
                             r.content.decode('utf-8')[0:2]])
    exchange_rates_df = pd.read_csv(io.StringIO(r.content.decode('utf-8')),
                     sep='|', skiprows=[0])
    # add column with date to which are Exchange Raters valid
    exchange_rates_df['date'] = request_date
    return exchange_rates_df

def complete_CNB_table(cnb_table):
    # change decimal separator to dot and convert string to float
    cnb_table['kurz'] = [x.replace(',', '.') for x in cnb_table['kurz']]
    cnb_table['kurz'] = cnb_table['kurz'].astype(float)
    cnb_table.columns = ['country', 'currency', 'amount_index', 'code',
                                 'rate', 'date']
    # add czech currency row
#    cnb_table = cnb_table.append(pd.Series(['Česko', 'koruna', 1, 'CZK', 1,
#                                               cnb_table['date'][1]]),
#                                ignore_index=True)
    cnb_table.loc[len(cnb_table)] = ['Česko', 'koruna', 1, 'CZK', 1,
                                               cnb_table['date'][0]]
    cnb_table.to_csv(''.join(['rates_tables/cnb_table_', cnb_table['date'][0], '.csv']),
                      sep=';', index=False)
    return cnb_table

def download_symbols_table():
    """
    """
    url = 'https://en.wikipedia.org/wiki/List_of_circulating_currencies'
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'lxml')
    table = soup.find("table", { "class" : "wikitable sortable" })

    html_header = table.find_all('tr')[0]
    html_rows = table.find_all('tr')[1:-1]
    
    text_header = [header.get_text() for header in html_header.find_all('th')]
    text_rows = [[item.get_text() for item in row.find_all('td')] for row in html_rows]
    # for multirows that have missing country value, insert the value from previous row
    for i in range(len(text_rows)):
        if len(text_rows[i]) == 5:
            text_rows[i].insert(0, text_rows[i-1][0])
    
    return pd.DataFrame(text_rows, columns = text_header)
    
def clean_symbols_table(raw_symbols_table):
    """
    """
    pd.options.mode.chained_assignment = None
    rename_df = raw_symbols_table.copy(deep=True)
    rename_df.columns = ['state', 'currency', 'symbol',
                       'code','fractional_unit', 'to_basic']
    # remove all brackets together with text using regex
    clean_df = rename_df.replace('\[[^]]*\]', '', regex=True)
    # remove symbols if there are more than one
    clean_df['symbol'] = clean_df['symbol'].replace('\s(.*)', '', regex=True)

    clean_df.to_csv('symbols_table/currencies_full.csv', sep=';', index=False)

    slice_df = clean_df.loc[:, ['currency', 'symbol', 'code']]

    deduplicated_df = slice_df.drop_duplicates(subset=['symbol', 'code'])
    deduplicated_df['symbol'][(deduplicated_df['currency'].str.contains('dollar')) 
                             & (deduplicated_df['code'] != 'USD')] = ''
    deduplicated_df['symbol'][(deduplicated_df['currency'].str.contains('pound')) 
                             & (deduplicated_df['code'] != 'GBP')] = ''
    deduplicated_df.to_csv('symbols_table/symbols_table.csv', sep=';', index=False)
    return deduplicated_df


# main function
def main():
    # parse input
    parser = argparse.ArgumentParser(description='Process \
                                     amount and currency input.')
    parser.add_argument('-a', '--amount', type = float, dest='amount',
                        help='amount of input currency money to be converted')
    parser.add_argument('-i', '--input_currency', dest='input_currency',
                        help='original currency, code or symbol')
    parser.add_argument('-o', '--output_currency', dest = 'output_currency',
                        default='ALL',
                        help='''desired currency for conversion \
                        (default: convert to all currencies possible)''')
    args = parser.parse_args()

    # create currency and conversion rates table
    create_directories('symbols_table', 'rates_tables')
    symbols_file = Path('symbols_table/symbols_table.csv')
    current_cnb_date = create_cnb_date('now')
    rates_file = Path(''.join(['rates_table/cnb_table_',
                               current_cnb_date, '.csv']))
    if symbols_file.is_file():
        symbols_df = pd.read_csv(symbols_file, sep=';')
    else:
        raw_symbols_df = download_symbols_table()
        symbols_df = clean_symbols_table(raw_symbols_df)
        
    if rates_file.is_file():
        rates_df = pd.read_csv(rates_file, sep=';')
    else:
       raw_rates_df = download_cnb_rates('now')
       rates_df = complete_CNB_table(raw_rates_df)
       
    symbol_rates_df = pd.merge(rates_df, symbols_df.iloc[:, 1:3],how='left',
                               left_on='code', right_on='code')
                               
    # pass arguments to object
    to_convert = ConvertMoney(args.amount, args.input_currency, args.output_currency)
    to_convert.get_current_rates(symbol_rates_df)
    parsed_json = json.dumps(to_convert.convert_currency(), indent = 4)
    print(parsed_json)
    
if __name__ == '__main__':
    main()
