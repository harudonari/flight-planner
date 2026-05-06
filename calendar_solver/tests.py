# Tests for solver.py
import pytest
import datetime
from solver import is_weekend, get_us_federal_holidays, is_vacation_day, count_vacation_days, parse_constraints

@pytest.fixture
def valid_raw():
    return {
        "vacation_days_remaining": 10,
        "year": 2026,
        "trips": [
            {
                "id": "trip1",
                "destination": "Tokyo",
                "departure_cities": ["NYC", "LAX"],
                "min_duration_days": 5
            },
            {
                "id": "trip2",
                "destination": "Chicago",
                "departure_cities": ["SFO"],
                "min_duration_days": 4
            }
        ],
        "blackout_dates": ["2026-01-01", "2026-12-25"],
        "earliest_start": "2026-05-01",
        "latest_end": "2026-12-31"
    }

def test_is_weekend_for_weekdays():
    assert not is_weekend(datetime.date(2024, 1, 1))  # Monday
    assert not is_weekend(datetime.date(2024, 1, 2))  # Tuesday
    assert not is_weekend(datetime.date(2024, 1, 3))  # Wednesday
    assert not is_weekend(datetime.date(2024, 1, 4))  # Thursday
    assert not is_weekend(datetime.date(2024, 1, 5))  # Friday

def test_is_weekend_returns_true_for_saturday():
    assert is_weekend(datetime.date(2024, 1, 6)) # Saturday

def test_is_weekend_returns_true_for_sunday():
    assert is_weekend(datetime.date(2024, 1, 7)) # Sunday

def test_get_us_federal_holidays_fixed_date():
    holidays_2026 = get_us_federal_holidays(2026)
    assert datetime.date(2026, 1, 1) in holidays_2026  # New Year's Day
    assert datetime.date(2026, 6, 19) in holidays_2026  # Juneteenth
    assert datetime.date(2026, 11, 11) in holidays_2026  # Veterans Day
    assert datetime.date(2026, 12, 25) in holidays_2026  # Christmas

def test_get_us_federal_holidays_nth_weekday():
    holidays_2026 = get_us_federal_holidays(2026)
    assert datetime.date(2026, 1, 19) in holidays_2026  # Martin Luther King, Jr. Day
    assert datetime.date(2026, 2, 16) in holidays_2026  # President's Day
    assert datetime.date(2026, 5, 25) in holidays_2026  # Memorial Day
    assert datetime.date(2026, 9, 7) in holidays_2026  # Labor Day
    assert datetime.date(2026, 10, 12) in holidays_2026  # Columbus Day
    assert datetime.date(2026, 11, 26) in holidays_2026  # Thanksgiving

def test_get_us_federal_holidays_saturday_observed_friday():
    holidays_2027 = get_us_federal_holidays(2027)
    assert datetime.date(2027, 6, 18) in holidays_2027  # Juneteenth observed on June 18, 2027
    assert datetime.date(2027, 12, 24) in holidays_2027  # Christmas observed on December 24, 2027

def test_get_us_federal_holidays_sunday_observed_monday():
    holidays_2027 = get_us_federal_holidays(2027)
    assert datetime.date(2027, 7, 5) in holidays_2027  # Independence Day observed on July 5, 2027

def test_is_vacation_day_weekday():
    holidays_2026 = get_us_federal_holidays(2026)
    assert is_vacation_day(datetime.date(2026, 1, 2), holidays_2026)   # Not a holiday
    assert is_vacation_day(datetime.date(2026, 1, 6), holidays_2026)  # Not a holiday
    assert is_vacation_day(datetime.date(2026, 1, 7), holidays_2026)  # Not a holiday

def test_is_vacation_day_weekend():
    holidays_2026 = get_us_federal_holidays(2026)
    assert not is_vacation_day(datetime.date(2026, 1, 3), holidays_2026)  # Saturday
    assert not is_vacation_day(datetime.date(2026, 5, 3), holidays_2026)  # Sunday

def test_is_vacation_day_holiday():
    holidays_2027 = get_us_federal_holidays(2027)
    assert not is_vacation_day(datetime.date(2027, 6, 18), holidays_2027) # Juneteenth observed on June 18, 2027
    assert not is_vacation_day(datetime.date(2027, 7, 5), holidays_2027) # Independence Day observed on July 5, 2027
    assert not is_vacation_day(datetime.date(2027, 12, 24), holidays_2027) # Christmas observed on December 24, 2027

def test_count_vacation_days_no_holidays():
    holidays_2026 = get_us_federal_holidays(2026)
    assert count_vacation_days(datetime.date(2026, 4, 30), datetime.date(2026, 5, 4), holidays_2026) == 3 # Apr 30 - May 1, May 4 are vacation days, May 2-3 are weekend

def test_count_vacation_days_with_holidays():
    holidays_2026 = get_us_federal_holidays(2026)
    assert count_vacation_days(datetime.date(2026, 1, 1), datetime.date(2026, 1, 10), holidays_2026) == 6  # Jan 1 is a holiday, Jan 2 is a vacation day, Jan 3-4 are weekends, Jan 5-9 are vacation days, Jan 10 is a weekend

def test_count_vacation_days_with_observed_holidays():
    holidays_2026 = get_us_federal_holidays(2026)
    assert count_vacation_days(datetime.date(2026, 7, 3), datetime.date(2026, 7, 5), holidays_2026) ==  0 # Jul 3 is a holiday, Jul 4-5 are weekends

def test_parse_constraints_valid_input(valid_raw):
    result = parse_constraints(valid_raw)
    assert result.vacation_days_remaining == 10
    assert result.year == 2026
    assert result.trips[0].id == "trip1"
    assert result.trips[0].destination == "Tokyo"
    assert result.trips[0].departure_cities == ["NYC", "LAX"]
    assert result.trips[0].min_duration_days == 5
    assert result.trips[1].id == "trip2"
    assert result.trips[1].destination == "Chicago"
    assert result.trips[1].departure_cities == ["SFO"]
    assert result.trips[1].min_duration_days == 4
    assert result.blackout_dates == {datetime.date(2026, 1, 1), datetime.date(2026, 12, 25)}
    assert result.earliest_start == datetime.date(2026, 5, 1)
    assert result.latest_end == datetime.date(2026, 12, 31)
    assert result.max_trips is None

def test_parse_constraints_with_max_trips(valid_raw):
    result = parse_constraints({**valid_raw, "max_trips": 2})
    assert result.max_trips == 2

def test_parse_constraints_invalid_max_trips_not_integer(valid_raw):
    with pytest.raises(ValueError, match="max_trips must be a positive integer if provided"):
        parse_constraints({**valid_raw, "max_trips": "not an integer"})

def test_parse_constraints_invalid_max_trips_zero(valid_raw):
    with pytest.raises(ValueError, match="max_trips must be a positive integer if provided"):
        parse_constraints({**valid_raw, "max_trips": 0})

def test_parse_constraints_invalid_max_trips_negative(valid_raw):
    with pytest.raises(ValueError, match="max_trips must be a positive integer if provided"):
        parse_constraints({**valid_raw, "max_trips": -1})

def test_parse_constraints_missing_vacation_days_remaining(valid_raw):
    del valid_raw["vacation_days_remaining"]
    with pytest.raises(ValueError, match="Missing required field: vacation_days_remaining"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_vacation_days_remaining_negative(valid_raw):
    with pytest.raises(ValueError, match="vacation_days_remaining must be a non-negative integer"):
        parse_constraints({**valid_raw, "vacation_days_remaining": -5})

def test_parse_constraints_invalid_vacation_days_remaining_not_integer(valid_raw):
    with pytest.raises(ValueError, match="vacation_days_remaining must be a non-negative integer"):
        parse_constraints({**valid_raw, "vacation_days_remaining": 2.5})

def test_parse_constraints_vacation_days_remaining_zero(valid_raw):
    result = parse_constraints({**valid_raw, "vacation_days_remaining": 0})
    assert result.vacation_days_remaining == 0

def test_parse_constraints_missing_year(valid_raw):
    del valid_raw["year"]
    with pytest.raises(ValueError, match="Missing required field: year"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_year(valid_raw):
    with pytest.raises(ValueError,  match="year must be a valid year between 1900 and 10 years from now"):
        parse_constraints({**valid_raw, "year": 20})

def test_parse_constraints_invalid_year_future(valid_raw):
    future_year = datetime.datetime.now().year + 20
    with pytest.raises(ValueError, match="year must be a valid year between 1900 and 10 years from now"):
        parse_constraints({**valid_raw, "year": future_year})

def test_parse_constraints_invalid_year_not_integer(valid_raw):
    with pytest.raises(ValueError, match="year must be a valid year between 1900 and 10 years from now"):
        parse_constraints({**valid_raw, "year": "not an integer"})
    
def test_parse_constraints_missing_trips(valid_raw):
    del valid_raw["trips"]
    with pytest.raises(ValueError, match="Missing required field: trips"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_trips_not_list(valid_raw):
    with pytest.raises(ValueError, match="trips must be a list of trip constraints"):
        parse_constraints({**valid_raw, "trips": "not a list"})

def test_parse_constraints_empty_trips_list(valid_raw):
    with pytest.raises(ValueError, match="trips must be a list of trip constraints"):
        parse_constraints({**valid_raw, "trips": []})

def test_parse_constraints_invalid_trip_missing_id(valid_raw):
    del valid_raw["trips"][0]["id"]
    with pytest.raises(ValueError, match="Missing required field: id"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_trip_duplicate_id(valid_raw):
    with pytest.raises(ValueError, match="Duplicate trip id: trip1"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": ["NYC", "LAX"],
            "min_duration_days": 5
        }, {
            "id": "trip1",  # duplicate id
            "destination": "Chicago",
            "departure_cities": ["SFO"],
            "min_duration_days": 4
        }]})

def test_parse_constraints_invalid_trip_missing_destination(valid_raw):
    del valid_raw["trips"][0]["destination"]
    with pytest.raises(ValueError, match="Missing required field: destination"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_trip_empty_destination(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 has an empty destination"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "departure_cities": ["NYC", "LAX"],
            "destination": "",
            "min_duration_days": 5
        }]})

def test_parse_constraints_invalid_trip_missing_departure_cities(valid_raw):
    del valid_raw["trips"][0]["departure_cities"]
    with pytest.raises(ValueError, match="Missing required field: departure_cities"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_trip_departure_cities_not_list(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 must have a non-empty list of departure cities"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": "not a list",
            "min_duration_days": 5
        }]})

def test_parse_constraints_invalid_trip_departure_cities_empty_list(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 must have a non-empty list of departure cities"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": [],
            "min_duration_days": 5
        }]})

def test_parse_constraints_invalid_trip_missing_min_duration_days(valid_raw):
    del valid_raw["trips"][0]["min_duration_days"]
    with pytest.raises(ValueError, match="Missing required field: min_duration_days"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_trip_min_duration_days_zero(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 must have a positive integer min_duration_days"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": ["NYC", "LAX"],
            "min_duration_days": 0
        }]})
def test_parse_constraints_invalid_trip_min_duration_days_negative(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 must have a positive integer min_duration_days"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": ["NYC", "LAX"],
            "min_duration_days": -3
        }]})

def test_parse_constraints_invalid_trip_min_duration_days_not_integer(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 must have a positive integer min_duration_days"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": ["NYC", "LAX"],
            "min_duration_days": 2.5
        }]})

def test_parse_constraints_invalid_blackout_dates_invalid_date_format(valid_raw):
    with pytest.raises(ValueError, match="Invalid date format for blackout_date 'invalid-date': expected YYYY-MM-DD"):
        parse_constraints({**valid_raw, "blackout_dates": ["2026-01-01", "invalid-date"]})

def test_parse_constraints_invalid_blackout_dates_not_a_list(valid_raw):
    with pytest.raises(ValueError, match="blackout_dates must be a list of date strings in YYYY-MM-DD format"):
        parse_constraints({**valid_raw, "blackout_dates": "not a list"})

def test_parse_constraints_no_blackout_dates(valid_raw):
    del valid_raw["blackout_dates"]
    result = parse_constraints(valid_raw)
    assert result.blackout_dates == set()

def test_parse_constraints_missing_earliest_start(valid_raw):
    del valid_raw["earliest_start"]
    with pytest.raises(ValueError, match="Missing required field: earliest_start"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_earliest_start_format(valid_raw):
    with pytest.raises(ValueError, match="Invalid date format for earliest_start '24-01-01': expected YYYY-MM-DD"):
        parse_constraints({**valid_raw, "earliest_start": "24-01-01"})

def test_parse_constraints_missing_latest_end(valid_raw):
    del valid_raw["latest_end"]
    with pytest.raises(ValueError, match="Missing required field: latest_end"):
        parse_constraints(valid_raw)

def test_parse_constraints_invalid_latest_end_format(valid_raw):
    with pytest.raises(ValueError, match="Invalid date format for latest_end '24-12-31': expected YYYY-MM-DD"):
        parse_constraints({**valid_raw, "latest_end": "24-12-31"})

def test_constraints_invalid_earliest_start_after_latest_end(valid_raw):
    with pytest.raises(ValueError, match="earliest_start must be before latest_end"):
        parse_constraints({**valid_raw, "earliest_start": "2026-12-31", "latest_end": "2026-05-01"})
