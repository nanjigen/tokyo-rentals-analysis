from suumo import *

def test_house_collector():
    expected_houses = 30
    # houses = house_collector(1, 2) # TODO use randint() = x-1
    # Check if the houses are collected correctly
    assert sum(1 for _ in house_collector(1, 2)) == 30
    # for house, expected_house in zip(houses, expected_houses):
    #     assert house.text.strip() == expected_house
