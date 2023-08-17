from suumo.suumo import *

def test_number_of_rental_listings():
    """Test if the expected number of rental listings are collected per page."""
    expected_listings = 30
    assert sum(1 for _ in collect_rental_listings(1, 2)) == expected_listings
