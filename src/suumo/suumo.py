# Tools for scraping SUUMO
# 
import requests, re
import json
# import pytest
from time import time, sleep
from random import randint
from bs4 import BeautifulSoup
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
fprop = fm.FontProperties(fname='/fonts/NotoSansCJKjp-Regular.otf')

import seaborn as sns
# sns.set(font='NotoSansCJKjp-Regular.otf')
sns.set(font='Noto Sans CJK JP')

from sqlalchemy import create_engine

plt.style.use('fivethirtyeight')
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
# import database

# [f for f in fm.fontManager.ttflist if 'Noto' in f.name]
# print(fm.matplotlib_fname())
# matplotlib.font_manager.findSystemFonts()
from matplotlib import pyplot as plt,font_manager as fm
from pathlib import Path
import os
#Restore the `.rcParams` from Matplotlib's internal default style.
plt.rcdefaults()

path = Path(os.getcwd())
# fname=os.path.join(path.parent.absolute(),'data','NotoSansCJKjp-Regular.otf')
fname=os.path.join(path.absolute(),'fonts','NotoSansCJKjp-Regular.otf')
fontProperties=fm.FontProperties(fname=fname,size=14)
default_font=fontProperties.get_name()# "Arial Unicode MS"
if default_font not in [f.name for f in fm.fontManager.ttflist]:
    print(f"{default_font} does not exist, let's add it to fontManager" )

if fname not in [f.fname for f in fm.fontManager.ttflist]:
    fm.fontManager.addfont(fname) # need absolute path

plt.rcParams['font.sans-serif']=[default_font]+plt.rcParams['font.sans-serif']
plt.rcParams['axes.unicode_minus']=False # in case minus sign is shown as box
# "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# Constants
# this is the URL generated after choosing specific search criteria on the website (e.g. location, house type, price range)
search_url = "http://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="
session = requests.Session()

def suumo_results_pages():
    """Return the number of pages generated by the search url"""
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content,"html.parser")
    page_nr = soup.find_all("ol", class_="pagination-parts")[-1].text
    page_nr = [int(s) for s in page_nr.split() if s.isdigit()]
    page_nr = page_nr[len(page_nr)-1]
    return page_nr

def collect_rental_listings(start_page, end_page):
    """Collect rental listings by looping through search result pages."""
    paginated_url = search_url + '&page='

    def fetch_listing_elements():
        for page in range(start_page, end_page):
            try:
                response = session.get(paginated_url + str(page))
                response.raise_for_status()  # Raise an exception if the request was not successful
                soup = BeautifulSoup(response.content,"html.parser")
                # "cassetteitem" is the class for each house
                yield from soup.select('div.cassetteitem')
                sleep(randint(1,3))
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while fetching page {page}: {e}")

    rental_listings = list(fetch_listing_elements())
    return rental_listings

def extract_detail_text(html):
    """Extract header data from outside table"""
    house_data = []
    for item in html:
        d = {}
        d["Title"] = item.find("div",{"class","cassetteitem_content-title"}).text
        d["Locality"] = item.find("li",{"class","cassetteitem_detail-col1"}).text
        house_data.append(d)
    return house_data

def extract_house_data(html):
    """Extract text from row data in table"""
    house_data = []
    for cassetteitem in html:
        table = cassetteitem.find('table',{'class','cassetteitem_other'})
        rows = table.find_all('tr', class_='js-cassette_link')
        for row in rows:
            columns = row.find_all('td')
            row_data = {
                'Title': extract_title(cassetteitem),
                'Locality': extract_locality(cassetteitem),
                'Floor': extract_floor(columns),
                'Rent': extract_rent(columns),
                'Admin Fee': extract_admin_fee(columns),
                'Deposit': extract_deposit(columns),
                'Key money': extract_key_money(columns),
                'Layout': extract_layout(columns),
                'Size': extract_size(columns),
                'ID': extract_id(columns),
                'Coordinates': extract_gps_location(row),
                'Link': extract_link(row),
            }
            house_data.append(row_data)
    return house_data

def extract_title(cassetteitem):
    return cassetteitem.find('div', {'class', 'cassetteitem_content-title'}).text

def extract_locality(cassetteitem):
    return cassetteitem.find('li', {'class', 'cassetteitem_detail-col1'}).text

def extract_floor(columns):
    return columns[2].get_text().strip()

def extract_rent(columns):
    return columns[3].find('span', class_='cassetteitem_price--rent').text

def extract_admin_fee(columns):
    admin_fee = columns[3].find('span', class_='cassetteitem_price--administration')
    return admin_fee.get_text().strip() if admin_fee else ''

def extract_deposit(columns):
    deposit = columns[4].find('span', class_='cassetteitem_price--deposit')
    return deposit.get_text().strip() if deposit else ''

def extract_key_money(columns):
    key_money = columns[4].find('span', class_='cassetteitem_price--gratuity')
    return key_money.get_text().strip() if key_money else ''

def extract_layout(columns):
    layout = columns[5].find('span', class_='cassetteitem_madori')
    return layout.get_text().strip() if layout else ''

def extract_size(columns):
    size = columns[5].find('span', class_='cassetteitem_menseki')
    return size.get_text().strip() if size else ''

def extract_id(columns):
    id_element = columns[0].select_one('.js-cassette_link input.js-single_checkbox')
    return id_element['value'] if id_element else ''

def extract_link(row):
    link = row.find('a', class_='js-cassette_link_href')
    return "https://suumo.jp" + link['href'] if link else ''
def extract_gps_location(row):
    link = extract_link(row)
    transformed_link = link.replace("/?", "/kankyo/?")
    r = requests.get(transformed_link)
    c = r.content
    soup = BeautifulSoup(c,"html.parser")
    if transformed_link:
            # Visit the transformed link and extract the HTML content
            # Assuming you have a way to make the HTTP request and retrieve the HTML content

            # Parse the HTML and find the script tag with id "js-gmapData"
            # Assuming `html_content` contains the HTML content
            script = soup.find('script', id='js-gmapData')

            if script:
                # Extract the JSON data within the script tag
                json_data = script.string

                # Parse the JSON data
                data = json.loads(json_data)

                # Extract the GPS coordinates
                if 'markers' in data and len(data['markers']) > 0:
                    lat = data['markers'][0]['lat']
                    lng = data['markers'][0]['lng']
                    return (lat, lng)

    return None

def load_data(start_page, end_page):
    """Load the data into a DataFrame for the given results page range."""
    try:
        extracted_data = extract_house_data(house_collector(start_page, end_page))
        # df = pd.DataFrame(extracted_data, columns=['Title', 'Locality', 'Floor', 'Size', 'Layout', 'Rent', {'Coordinates': [('lat', 'long'), (1, 2)]}, 'ID', 'Link'])
        df = pd.DataFrame(extracted_data, columns=['Title', 'Locality', 'Floor', 'Size', 'Layout', 'Rent', 'Coordinates', 'ID', 'Link'])
        # df[['lat', 'long']] = df['Coordinates'].apply(pd.Series)[0]==2
        df[['lat', 'long']] = df['Coordinates'].apply(lambda x: pd.Series(x))
        df.drop('Coordinates', axis=1, inplace=True)
        return df
    except Exception as e:
        print(f"Error occurred while loading data: {e}")
        return None


def clean_numeric_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe generated by scraping to address inconsistencies, missing values, and outliers.

    Args:
        dataframe (pd.DataFrame): The input DataFrame to be cleaned.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    if not isinstance(dataframe, (pd.DataFrame, pd.Series)):
        raise ValueError("Input must be a Pandas DataFrame or Series.")

    df = dataframe.copy()

    # Pre-compile regular expressions
    # decimal_value = re.compile(r'(\d+(?:\.\d+)?)')
    decimal_value = r'(\d+(?:\.\d+)?)'
    int_value = re.compile(r'\d+')

    # Check if respective column needs cleaning
    if not df.empty:
        # if not len(df) == 0:
        if df['Floor'].str.contains("階").any():
            df['Floor'] = df['Floor'].apply(lambda x: re.findall(int_value, x)[0]
                                            if re.findall(int_value, x)
                                            else '')
            df['Rooms'] = df['Layout'].apply(lambda x: re.findall(int_value, x)[0]
                                        if re.findall(int_value, x)
                                        else '1' if 'ワンルーム' in x
                                        else '')
        if df['Size'].str.contains("m2").any():
            df['Size'] = df['Size'].apply(lambda x: re.findall(decimal_value, x)[0]
                                        if re.findall(decimal_value, x)
                                        else '')
        if df['Rent'].str.contains("円").any():
            df['Rent'] = (df['Rent'].str.extract(decimal_value, expand=False)
                          .astype(float)
                          .mul(10000)
                          .astype(int))
        return df


def create_database(db, table, start_page, end_page):
    engine = create_engine('sqlite:///%s' %db, echo=True)
    sqlite_table = table
    sqlite_connection = engine.connect()

   # Load data, clean numeric values, and write to SQLite database
    df_database = (load_data(start_page, end_page)
                  .pipe(clean_numeric_data))

    df_database.to_sql(sqlite_table, sqlite_connection, if_exists='replace', index=False)

    sqlite_connection.close()
