from suumo.suumo import *

@pytest.fixture
def search_url():
    return "http://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="

def test_search_results(search_url):
    """Test the number of returned search results against results per page * page count"""
    expected_result_count = fetch_results_total_hits(search_url)
    calculated_result_count = fetch_results_per_page(search_url) * fetch_total_pages_count(search_url)
    assert expected_result_count == calculated_result_count, \
        f"Expected {expected_result_count} results, but got {calculated_result_count} caculated results."

def test_number_of_rental_listings():
    """Test if the expected number of rental listings are collected per page."""
    expected_listings = 30
    assert sum(1 for _ in collect_rental_listings(search_url, 1, 2)) == expected_listings
