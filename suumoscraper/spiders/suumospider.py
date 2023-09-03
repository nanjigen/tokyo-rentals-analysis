import scrapy

class SuumoSpider(scrapy.Spider):
    name = "suumospider"
    allowed_domains = ['suumo.jp']
    # this is the old URL generated after choosing specific search criteria on the website (e.g. location, house type, price range)
    start_urls = [
        "http://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="
    ]

    def parse(self, response: HtmlResponse):
        total_pages = self.get_total_pages(response)
        self.logger.info(f"Total Pages: {total_pages}")
    
        total_hits = self.get_total_hits(response)
        self.logger.info(f"Total Hits: {total_hits}")
    
        results_per_page = self.get_results_per_page(response)
        self.logger.info(f"Results Per Page: {results_per_page}")
    

    def get_total_pages(self, response: HtmlResponse) -> int:
        page_button_text = response.css("ol.pagination-parts li a::text").getall()[-1]
        return int(page_button_text) if page_button_text else 0
    
    def get_total_hits(self, response: HtmlResponse) -> int:
        div_element = response.css("div.pagination_set-hit::text").get().strip()
        return int(div_element.replace(",", "")) if div_element else 0
    
    def get_results_per_page(self, response: HtmlResponse) -> int:
        selected_option_value = response.css(
            "select#js-tabmenu2-pcChange option[selected]::attr(value)"
        ).get()
        return int(selected_option_value) if selected_option_value else 0
    
    def collect_rental_listings(search_url, start_page, end_page):
        """Collect rental listings by looping through search result pages."""
        paginated_url = search_url + '&page='
    
        def fetch_listing_elements():
            for page in range(start_page, end_page):
                try:
                    response = session.get(paginated_url + str(page))
                    response.raise_for_status()  # Raise an exception if the request was not successful
                    soup = BeautifulSoup(response.content,"html.parser")
                    # "cassetteitem" is the class for each rental
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
    
    def extract_floor(cassetteitem):
        columns = cassetteitem.find_all('td')
        return columns[2].get_text().strip()
    
    def extract_rent(cassetteitem):
        columns = cassetteitem.find_all('td')
        return columns[3].find('span', class_='cassetteitem_price--rent').text
    
    def extract_admin_fee(cassetteitem):
        columns = cassetteitem.find_all('td')
        admin_fee = columns[3].find('span', class_='cassetteitem_price--administration')
        return admin_fee.get_text().strip() if admin_fee else ''
    
    def extract_deposit(cassetteitem):
        columns = cassetteitem.find_all('td')
        deposit = columns[4].find('span', class_='cassetteitem_price--deposit')
        return deposit.get_text().strip() if deposit else ''
    
    def extract_key_money(cassetteitem):
        columns = cassetteitem.find_all('td')
        key_money = columns[4].find('span', class_='cassetteitem_price--gratuity')
        return key_money.get_text().strip() if key_money else ''
    
    def extract_layout(cassetteitem):
        columns = cassetteitem.find_all('td')
        layout = columns[5].find('span', class_='cassetteitem_madori')
        return layout.get_text().strip() if layout else ''
    
    def extract_size(cassetteitem):
        columns = cassetteitem.find_all('td')
        size = columns[5].find('span', class_='cassetteitem_menseki')
        return size.get_text().strip() if size else ''
    
    def extract_link(cassetteitem):
        row = cassetteitem.find('tr', class_='js-cassette_link')
        link = row.find('a', class_='js-cassette_link_href')
        return "https://suumo.jp" + link['href'] if link else ''
    
    def load_data(start_page, end_page):
        """Load the data into a DataFrame for the given results page range."""
        try:
            extracted_data = extract_house_data(house_collector(start_page, end_page))
            df = pd.DataFrame(extracted_data, columns=['Title', 'Locality', 'Floor', 'Size', 'Layout', 'Rent', 'Link'])
            return df
        except Exception as e:
            print(f"Error occurred while loading data: {e}")
            return None
