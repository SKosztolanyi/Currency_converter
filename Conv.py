#!/home/pista/anaconda3/bin/python

# source of argparse: https://docs.python.org/3.3/library/argparse.html
import os
import io
import datetime
import string
import simplejson as json
import argparse
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description='Process \
                                 amount and currency input.')
parser.add_argument('-a', '--amount', dest='amount')
parser.add_argument('-i', '--input_currency', dest='input_currency',
                    help='original currency, code or symbol')
parser.add_argument('-o', '--output_currency', dest = 'output_currency',
                    default='All',
                    help='desired currency for conversion (default: convert to all)')

args = parser.parse_args()
print(args)

#check:
#    if not in codes or symbol, print error, break (symbol is len 1, code is len3)

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
        self.input_rate = rates_table['rate'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
        self.output_rate = rates_table['rate'][(rates_table['code'] == self.out_curr_symbol) |
                                        (rates_table['symbol'] == self.out_curr_symbol)].values
        self.input_index = rates_table['amount_index'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
        self.output_index = rates_table['amount_index'][(rates_table['code'] == self.out_curr_symbol) |
                                        (rates_table['symbol'] == self.out_curr_symbol)].values
        self.input_currency = rates_table['code'][(rates_table['code'] == self.in_curr_symbol) |
                                        (rates_table['symbol'] == self.in_curr_symbol)].values[0]
        self.output_currency = rates_table['code'][(rates_table['code'] == self.out_curr_symbol) |
                                        (rates_table['symbol'] == self.out_curr_symbol)].values
        rates_table['CZK_amount'] = self.amount/self.input_index*self.input_rate
        rates_table['converted_amount'] = (rates_table['CZK_amount']*rates_table['amount_index']/
                                          rates_table['rate']).round(2)
        self.output_table = rates_table.loc[:,['code', 'converted_amount']]
        self.rates_table = rates_table
                     
    def convert_currency(self):
        CZK_amount = self.amount/self.input_index*self.input_rate
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
            output_amount = float(round(CZK_amount/(self.output_index*self.output_rate), 2))
            full_json['output'][self.output_currency] = output_amount
        #TODO make it work for more than 1 output       
        return full_json

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
    cnb_table.to_csv(''.join(['cnb_table_', cnb_table['date'][0], '.csv']),
                      sep=';', index=False)
    return cnb_table
    
    


# Save the DF as csv with date in name. Check if it exists, if yes, read from file
# if not, read online and save it as a new file

rates_df = download_cnb_rates('2017-08-08')
complete_rates = complete_CNB_table(rates_df)
# save the table
complete_rates.to_csv(''.join(['cnb_table_', complete_rates['date'][0], '.csv']),
                      sep=';', index=False)
                      
# pretty printing result output

       
sim = ConvertMoney(100, 'EUR', 'USD')
sim.amount
sim.input_currency
sim.get_current_rates(complete_rates)

parsed_json = json.dumps(sim.get_current_rates(complete_rates), indent = 4)
print(parsed_json)

# TODO: do a check if the table with the date exists. 
# If yes, read it from csv
# If no, download it from website

# converter function:

# Download table from wikipedia
url = 'https://en.wikipedia.org/wiki/List_of_circulating_currencies'
req = requests.get(url)
soup = BeautifulSoup(req.content, 'lxml')
table = soup.find("table", { "class" : "wikitable sortable" })

print(table)

def remove_forbidden_strings(list_to_clean, forbidden_list):
    """ Returns a clean list without elements contained in fobridden_list.
    """
    for el in list_to_clean:
        if el in forbidden_list:
            list_to_clean.remove(el)
    return list_to_clean
        
def cast_list_to_string(input_list = []):
    """ Returns the first element of a list as a trimmed string. """
    # if there are two elements possible, take only the first one
    return(''.join(input_list).split('or')[0])

# these are just Wikipedia note signs and should be removed from list of values


# parsing step
clean_tuples_list = []
for row in table.findAll("tr"):
    cells = row.findAll("td")
    print(cells[0:4])
    # parse only those arguments that are not empty
    if len(cells[1:4]) == 3:
        currency = cells[1].findAll(text=True)
        symbol = cells[2].findAll(text=True)
        code = cells[3].findAll(text=True)
        # cleaning step
        currency = cast_list_to_string(
                remove_forbidden_strings(currency, forbidden_chars))
        symbol = cast_list_to_string(
                remove_forbidden_strings(symbol, forbidden_chars))
        code = cast_list_to_string(
                remove_forbidden_strings(code, forbidden_chars)) 
        # append only those that don't have symbol value at currency
#        if len(currency) > 3:
#            clean_tuples_list.append((currency.strip(), 
#                                      symbol.strip(), 
#                                      code.strip()))
#        else:
        print(currency, symbol, code)

saved_rowspans = []
for row in table.findAll("tr"):
    cells = row.findAll(["td"])

    if len(saved_rowspans) == 0:
        saved_rowspans = [None for _ in cells]
        
    for index, cell in enumerate(cells):
        if cell.has_attr("rowspan"):
            rowspan_data = {
                'rows_left': int(cell["rowspan"]),
                'value': cell,
            }
            saved_rowspans[index] = rowspan_data
        elif len(cells) != len(saved_rowspans):
            for index, rowspan_data in enumerate(saved_rowspans):
                if rowspan_data is not None:
                    # Insert the data from previous row; decrement rows left
                    cells.insert(index, rowspan_data['value'])
        
                    if saved_rowspans[index]['rows_left'] == 1:
                        saved_rowspans[index] = None
                    else:
                        saved_rowspans[index]['rows_left'] -= 1

# source: https://roche.io/2016/05/scrape-wikipedia-with-python

# Download table from wikipedia
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
    updated_rows = [text_rows[i].insert(0, text_rows[i-1][0]) if len(text_rows[i]) == 5 
                    else text_rows[i] for i in range(len(text_rows))]
    return updated_rows
    
def clean_symbols_table(raw_symbols_table):
    """
    """
    rename_df = pd.DataFrame(raw_symbols_table, 
                             columns=['state', 'currency', 'symbol',
                                      'ISO','fractional_unit', 'to_basic'])
    # remove all brackets together with text using regex
    clean_df = rename_df.replace('\[[^]]*\]', '', regex=True)
    # remove symbols if there are more than one
    clean_df['symbol'] = clean_df['symbol'].replace('\s(.*)', '', regex=True)

    clean_df.to_csv('currencies_full.csv', sep=';', index=False)

    slice_df = clean_df.loc[:, ['currency', 'symbol', 'ISO']]

    deduplicated_df = slice_df.drop_duplicates(subset=['symbol', 'ISO'])
    deduplicated_df['symbol'][(deduplicated_df['currency'].str.contains('dollar')) 
                             & (deduplicated_df['ISO'] != 'USD')] = ''
    deduplicated_df['symbol'][(deduplicated_df['currency'].str.contains('pound')) 
                             & (deduplicated_df['ISO'] != 'GBP')] = ''
    deduplicated_df.to_csv('symbols_table/symbols_table.csv', sep=';', index=False)
    return deduplicated_df
# where currency like dollar and ISO not like USD, symbol = ''

rates_symbol = pd.merge(complete_rates, currencies_deduplicated_df.iloc[:,1:3], how='left', 
                    left_on='code', right_on='ISO')

# subset on currency with or statmeent
rates_symbol['kurz'][(rates_symbol['ISO'] == '£') | (rates_symbol['symbol'] == '£')]

rates_symbol['kurz'][(rates_symbol['ISO'] == 'CZK') | (rates_symbol['symbol'] == 'CZK')]

to_convert = ConvertMoney(args.amount, args.input_currency, args.output_currency)
to_convert.input_currency

sim = ConvertMoney(100, 'USD', 'CZK')
sim.amount
sim.input_currency
sim.get_current_rates(rates_symbol)
sim.output_index
sim.output_currency
sim.input_rate
sim.convert_currency()


forbidden_elements = ['\xa0', '[E]', '[F]', '[G]', '[H]', '[I]', '[J]', '[K]', 
                      '[L]', '[M]']

for i in range(len(text_rows)):
    if len(text_rows[i]) == 5:
        text_rows[i].insert(0, text_rows[i-1][0])



for no, tr in enumerate(allRows):
    tmp = []
    for td_no, data in enumerate(tr.find_all('td')):
        print(data.has_attr("rowspan"))
        if data.has_attr("rowspan"):
            rowspan.append((no, td_no, int(data["rowspan"]), data.get_text()))


if rowspan:
    for i in rowspan:
        # tr value of rowspan in present in 1th place in results
        for j in range(1, i[2]):
            #- Add value in next tr.
            results[i[0]+j].insert(i[1], i[3])


dfdf = pd.DataFrame(data=results, columns=headers)


# deduplicate the table and save results to csv
currencies_symbols = pd.DataFrame(clean_tuples_list, 
                                  columns=['currency', 'symbol', 'code'])
currencies_deduplicated = currencies_symbols.drop_duplicates()
currencies_deduplicated.to_csv('symbols_table.csv', sep=';', index=False)

joinerka = pd.merge(df, currencies_deduplicated.iloc[:,1:3], how='left', 
                    left_on='kód', right_on='code')
                    
#  how to use it for all?
symbol_rates_df['amount_index'][(symbol_rates_df['code'] == 'EUR') |
                                        (symbol_rates_df['symbol'] == 'EUR')].values[0]

ss = symbol_rates_df['amount_index'][(symbol_rates_df['code'] == 'EUR') |
                                        (symbol_rates_df['symbol'] == 'EUR')].values
                                        
ss = symbol_rates_df['amount_index'][(symbol_rates_df['code'] == 'ALL') |
                                        (symbol_rates_df['symbol'] == 'ALL')].values

def main():
    # parse imput
    parser = argparse.ArgumentParser(description='Process \
                                     amount and currency input.')
    parser.add_argument('-a', '--amount', dest='amount')
    parser.add_argument('-i', '--input_currency', dest='input_currency',
                        help='original currency, code or symbol')
    parser.add_argument('-o', '--output_currency', dest = 'output_currency',
                        default='All',
                        help='desired currency for conversion (default: convert to all)')
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
    to_convert = ConvertMoney(100, 'EUR', 'ALL')
    
    to_convert.get_current_rates(symbol_rates_df)
#    to_convert.output_index
#    to_convert.output_currency
#    to_convert.input_rate
    parsed_json = json.dumps(to_convert.convert_currency(),
                             indent = 4, sort_keys=True, use_decimal=True)
    print(parsed_json)
    
if __name__ == '__main__':
    main()
                               
            



















