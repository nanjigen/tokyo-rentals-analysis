from suumo.suumo import *

def test_search_results(response):
    """Test the number of returned search results against results per page * page count"""
    expected_result_count = SuumoSpider().get_total_hits(response)
    calculated_result_count = SuumoSpider().get_results_per_page(response) * SuumoSpider().get_total_pages(response)
    assert expected_result_count == calculated_result_count, \
        f"Expected {expected_result_count} results, but got {calculated_result_count} caculated results."

def test_number_of_rental_listings():
    """Test if the expected number of rental listings are collected per page."""
    expected_listings = 30
    assert sum(1 for _ in collect_rental_listings(search_url, 1, 2)) == expected_listings
