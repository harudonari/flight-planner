# Tests for solver.py
import datetime
from solver import is_weekend, get_us_federal_holidays, is_vacation_day, count_vacation_days

def test_is_weekend():
    assert is_weekend(datetime.date(2024, 1, 1)) == False  # Monday
    assert is_weekend(datetime.date(2024, 1, 2)) == False  # Tuesday
    assert is_weekend(datetime.date(2024, 1, 3)) == False  # Wednesday
    assert is_weekend(datetime.date(2024, 1, 4)) == False  # Thursday
    assert is_weekend(datetime.date(2024, 1, 5)) == False  # Friday
    assert is_weekend(datetime.date(2024, 1, 6)) == True # Saturday
    assert is_weekend(datetime.date(2024, 1, 7)) == True # Sunday

def test_get_us_federal_holidays():
    holidays_2026 = get_us_federal_holidays(2026)
    assert datetime.date(2026, 1, 1) in holidays_2026  # New Year's Day
    assert datetime.date(2026, 1, 19) in holidays_2026  # Martin Luther King, Jr. Day
    assert datetime.date(2026, 2, 16) in holidays_2026  # President's Day
    assert datetime.date(2026, 5, 25) in holidays_2026  # Memorial Day
    assert datetime.date(2026, 6, 19) in holidays_2026  # Juneteenth
    assert datetime.date(2026, 7, 3) in holidays_2026  # Independence Day
    assert datetime.date(2026, 9, 7) in holidays_2026  # Labor Day
    assert datetime.date(2026, 10, 12) in holidays_2026  # Columbus Day
    assert datetime.date(2026, 11, 11) in holidays_2026  # Veterans Day
    assert datetime.date(2026, 11, 26) in holidays_2026  # Thanksgiving
    assert datetime.date(2026, 12, 25) in holidays_2026  # Christmas

def test_is_vacation_day():
    holidays_2026 = get_us_federal_holidays(2026)
    assert is_vacation_day(datetime.date(2026, 1, 1), holidays_2026) == False  # New Year's Day
    assert is_vacation_day(datetime.date(2026, 1, 2), holidays_2026) == True   # Not a holiday
    assert is_vacation_day(datetime.date(2026, 1, 3), holidays_2026) == False   # Saturday
    assert is_vacation_day(datetime.date(2026, 1, 6), holidays_2026) == True  # Not a holiday
    assert is_vacation_day(datetime.date(2026, 1, 7), holidays_2026) == True  # Not a holiday

    holidays_2027 = get_us_federal_holidays(2027)
    assert is_vacation_day(datetime.date(2027, 6, 18), holidays_2027) == False # Juneteenth observed on June 18, 2027
    assert is_vacation_day(datetime.date(2027, 7, 5), holidays_2027) ==  False # Independence Day observed on July 5, 2027
    assert is_vacation_day(datetime.date(2027, 12, 24), holidays_2027) == False # Christmas observed on December 24, 2027

def test_count_vacation_days():
    holidays_2026 = get_us_federal_holidays(2026)
    assert count_vacation_days(datetime.date(2026, 1, 1), datetime.date(2026, 1, 10), holidays_2026) == 6  # Jan 1 is a holiday, Jan 2 is a vacation day, Jan 3-4 are weekends, Jan 5-9 are vacation days, Jan 10 is a weekend
    assert count_vacation_days(datetime.date(2026, 6, 18), datetime.date(2026, 6, 20), holidays_2026) == 1 # Jun 18 is a vacation day, Jun 19-20 are holiday & weeked
    assert count_vacation_days(datetime.date(2026, 12, 22), datetime.date(2026, 12, 28), holidays_2026) == 4 # Dec 22-24 are vacation days, Dec 25 is a holiday, December 26-27 are weekends, Dec 28 is a vacation day


if __name__ == "__main__":
    test_is_weekend()
    test_get_us_federal_holidays()
    test_is_vacation_day()
    test_count_vacation_days()
    print("All tests passed!")