# Tests for solver.py
import pytest
import datetime
from solver import *
from agent import *


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

@pytest.fixture
def valid_constraints():
    return parse_constraints({
        "vacation_days_remaining": 10,
        "year": 2026,
        "trips": [
            {"id": "trip1",
            "destination": "Chicago",
            "departure_cities": ["NYC", "LAX"],
            "min_duration_days": 4
        }],
        "blackout_dates": ["2026-01-01", "2026-12-25", "2026-05-08"],
        "earliest_start": "2026-05-01",
        "latest_end": "2026-05-31"
    })

@pytest.fixture
def small_constraints():
    return SolverConstraints(
        vacation_days_remaining=10,
        year=2026,
        trips=[
            TripConstraint(
                id="trip1",
                destination="Chicago",
                departure_cities=["NYC", "LAX"],
                min_duration_days=3
            )
        ],
        blackout_dates={datetime.date(2026, 1, 1), datetime.date(2026, 12, 25), datetime.date(2026, 5, 6)},
        earliest_start=datetime.date(2026, 5, 1),
        latest_end=datetime.date(2026, 5, 7),
        max_trips=None
    )

@pytest.fixture
def valid_windows_one_to_seventh():
    return [
        Window(
            trip_id="trip1",
            start_date=datetime.date(2026, 5, 1),
            end_date=datetime.date(2026, 5, 3),
            vacation_days_cost=1,
            weekend_anchored=True,
            overlaps_holiday=False,
            total_days=3
        ),
        Window(
            trip_id="trip1",
            start_date=datetime.date(2026, 5, 2),
            end_date=datetime.date(2026, 5, 4),
            vacation_days_cost=1,
            weekend_anchored=True,
            overlaps_holiday=False,
            total_days=3
        ),
        Window(
            trip_id="trip1",
            start_date=datetime.date(2026, 5, 3),
            end_date=datetime.date(2026, 5, 5),
            vacation_days_cost=2,
            weekend_anchored=False,
            overlaps_holiday=False,
            total_days=3
    )]

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

def test_parse_constraints_invalid_max_trips_bool(valid_raw):
    with pytest.raises(ValueError, match="max_trips must be a positive integer if provided"):
        parse_constraints({**valid_raw, "max_trips": True})

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

def test_parse_constraints_invalid_vacation_days_remaining_bool(valid_raw):
    with pytest.raises(ValueError, match="vacation_days_remaining must be a non-negative integer"):
        parse_constraints({**valid_raw, "vacation_days_remaining": True})

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

def test_parse_constraints_invalid_year_bool(valid_raw):
    with pytest.raises(ValueError, match="year must be a valid year between 1900 and 10 years from now"):
        parse_constraints({**valid_raw, "year": True})

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

def test_parse_constraints_invalid_trip_min_duration_days_bool(valid_raw):
    with pytest.raises(ValueError, match="Trip trip1 must have a positive integer min_duration_days"):
        parse_constraints({**valid_raw, "trips": [{
            "id": "trip1",
            "destination": "Tokyo",
            "departure_cities": ["NYC", "LAX"],
            "min_duration_days": True
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

def test_is_weekend_anchored_start_on_friday():
    assert is_weekend_anchored(datetime.date(2026, 5, 1), datetime.date(2026, 5, 6))  # Starts on Friday

def test_is_weekend_anchored_start_on_saturday():
    assert is_weekend_anchored(datetime.date(2026, 5, 2), datetime.date(2026, 5, 7))  # Starts on Saturday

def test_is_weekend_anchored_end_on_sunday():
    assert is_weekend_anchored(datetime.date(2026, 5, 7), datetime.date(2026, 5, 10))  # Ends on Sunday    

def test_is_weekend_anchored_end_on_monday():
    assert is_weekend_anchored(datetime.date(2026, 5, 7), datetime.date(2026, 5, 11))  # Ends on Monday

def test_is_weekend_anchored_not_weekend_anchored():
    assert not is_weekend_anchored(datetime.date(2026, 5, 6), datetime.date(2026, 5, 9))  # Starts on Wednesday, ends on Saturday

def test_generate_windows_basic(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    assert len(windows) > 0

def test_generate_windows_include_fri_to_mon(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    assert any(window.start_date.weekday() == 4 and window.end_date.weekday() == 0 for window in windows)  # Fri to Mon

def test_generate_windows_exclude_blackout_date(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    for window in windows:
        assert datetime.date(2026, 5, 8) not in (window.start_date + datetime.timedelta(days=i) for i in range(window.total_days))

def test_generate_windows_weekend_anchored(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    for window in windows:
        if window.weekend_anchored:
            assert window.start_date.weekday() in (4, 5) or window.end_date.weekday() in (6, 0)

def test_generate_windows_overlaps_holiday(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    for window in windows:
        if window.overlaps_holiday:
            assert any((window.start_date + datetime.timedelta(days=i)) in holidays for i in range(window.total_days))

def test_generate_windows_vacation_days_cost(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    for window in windows:
        expected_cost = count_vacation_days(window.start_date, window.end_date, holidays)
        assert window.vacation_days_cost == expected_cost

def test_generate_windows_total_days(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    for window in windows:
        assert window.total_days == valid_constraints.trips[0].min_duration_days

def test_generate_windows_valid_window(valid_constraints):
    holidays = get_us_federal_holidays(valid_constraints.year)
    windows = generate_windows(valid_constraints.trips[0], valid_constraints, holidays)
    for window in windows:
        assert window.start_date >= valid_constraints.earliest_start
        assert window.end_date <= valid_constraints.latest_end

def test_generate_windows_min_duration_exceeds_range(small_constraints):
    # Trip is longer than the entire search window
    long_trip = TripConstraint(id="trip1", destination="X", departure_cities=["A"], min_duration_days=100)
    holidays = get_us_federal_holidays(small_constraints.year)
    assert generate_windows(long_trip, small_constraints, holidays) == []

def test_generate_windows_blackout_at_start(small_constraints):
    # Blackout on earliest_start — pointer should advance past it
    blocked = SolverConstraints(**{**small_constraints.__dict__, 
        "blackout_dates": {small_constraints.earliest_start}})
    holidays = get_us_federal_holidays(small_constraints.year)
    windows = generate_windows(small_constraints.trips[0], blocked, holidays)
    for w in windows:
        assert w.start_date > small_constraints.earliest_start

def test_generate_windows_all_dates_blacked_out(small_constraints):
    all_dates = {small_constraints.earliest_start + datetime.timedelta(days=i) 
                 for i in range((small_constraints.latest_end - small_constraints.earliest_start).days + 1)}
    blocked = SolverConstraints(**{**small_constraints.__dict__, "blackout_dates": all_dates})
    holidays = get_us_federal_holidays(small_constraints.year)
    assert generate_windows(small_constraints.trips[0], blocked, holidays) == []

def test_score_window_valid_score_clamping(small_constraints):
    holidays = get_us_federal_holidays(small_constraints.year)
    windows = generate_windows(small_constraints.trips[0], small_constraints, holidays)
    for window in windows:
        score = score_window(window, small_constraints.earliest_start, small_constraints.latest_end)
        assert 0.0 <= score <= 1.0

def test_score_window_correct_score(valid_windows_one_to_seventh):
    earliest_start = datetime.date(2026, 5, 1)
    latest_end = datetime.date(2026, 5, 7)
    scores = [score_window(window, earliest_start, latest_end) for window in valid_windows_one_to_seventh]
    assert scores[0] > scores[1] > scores[2]

def test_score_window_max_score():
    earliest_start = datetime.date(2026, 5, 1)
    latest_end = datetime.date(2026, 5, 7)
    window = Window(
        trip_id="trip1",
        start_date=earliest_start,
        end_date=datetime.date(2026, 5, 3),
        total_days=3,
        vacation_days_cost=0,
        weekend_anchored=True,
        overlaps_holiday=False)
    assert score_window(window, earliest_start, latest_end) == 1.0

def test_score_window_single_day_window():
    date = datetime.date(2026, 5, 1)
    window = Window(
        trip_id="trip1",
        start_date=date,
        end_date=date,
        total_days=1,
        vacation_days_cost=1,
        weekend_anchored=False,
        overlaps_holiday=False)
    score = score_window(window, date, date)
    assert 0.0 <= score <= 1.0

def test_rank_windows_pruning_and_sorting(small_constraints):
    holidays = get_us_federal_holidays(small_constraints.year)
    windows = generate_windows(small_constraints.trips[0], small_constraints, holidays)
    ranked_windows = rank_windows(windows, small_constraints)
    for window in ranked_windows:
        assert window.vacation_days_cost <= small_constraints.vacation_days_remaining
    for i in range(len(ranked_windows) - 1):
        score_i = score_window(ranked_windows[i], small_constraints.earliest_start, small_constraints.latest_end)
        score_next = score_window(ranked_windows[i + 1], small_constraints.earliest_start, small_constraints.latest_end)
        assert score_i >= score_next

def test_rank_windows_empty_input(small_constraints):
    assert rank_windows([], small_constraints) == []

def test_rank_windows_all_pruned(small_constraints):
    # All windows exceed the budget
    tight = SolverConstraints(**{**small_constraints.__dict__, "vacation_days_remaining": 0})
    holidays = get_us_federal_holidays(small_constraints.year)
    windows = generate_windows(small_constraints.trips[0], small_constraints, holidays)
    # filter to only windows that would cost > 0
    assert rank_windows(windows, tight) == []

def test_find_non_overlapping_combinations_no_overlap():
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False)],
        "trip2": [Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=5, weekend_anchored=False, overlaps_holiday=False)],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 10)
    assert len(result) == 1
    assert {w.trip_id for w in result[0].windows} == {"trip1", "trip2"}

def test_find_non_overlapping_combinations_with_overlap():
    # trip1 and trip2 overlap, but trip2 has a second non-overlapping window
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False)],
        "trip2": [
            Window(trip_id="trip2", start_date=datetime.date(2026, 5, 3), end_date=datetime.date(2026, 5, 7), total_days=5, vacation_days_cost=4, weekend_anchored=False, overlaps_holiday=False),  # overlaps trip1
            Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=5, weekend_anchored=False, overlaps_holiday=False),  # no overlap
        ],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 10)
    assert len(result) == 1
    trip2_window = next(w for w in result[0].windows if w.trip_id == "trip2")
    assert trip2_window.start_date == datetime.date(2026, 6, 1)

def test_find_non_overlapping_combinations_with_overlap_other_way():
    # trip1 and trip2 overlap, but trip1 has a secondnon-overlapping window
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 29), end_date=datetime.date(2026, 6, 1), total_days=4, vacation_days_cost=2, weekend_anchored=True, overlaps_holiday=False),
                  Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False)], # overlaps trip2
        "trip2": [Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=5, weekend_anchored=False, overlaps_holiday=False)],  # no overlap
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 10)
    assert len(result) == 1
    trip1_window = next(w for w in result[0].windows if w.trip_id == "trip1")
    assert trip1_window.start_date == datetime.date(2026, 5, 1)

def test_find_non_overlapping_combinations_exceed_budget():
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False)],
        "trip2": [Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=5, weekend_anchored=False, overlaps_holiday=False)],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 5)
    assert len(result) == 0

def test_find_non_overlapping_combinations_caps_at_20():
    trip1_windows = [
        Window(trip_id="trip1", start_date=datetime.date(2026, m, 1), end_date=datetime.date(2026, m, 5),
               total_days=5, vacation_days_cost=1, weekend_anchored=False, overlaps_holiday=False, score=1.0)
        for m in [1, 3, 5, 7, 9, 11]
    ]
    trip2_windows = [
        Window(trip_id="trip2", start_date=datetime.date(2026, m, 1), end_date=datetime.date(2026, m, 5),
               total_days=5, vacation_days_cost=1, weekend_anchored=False, overlaps_holiday=False, score=1.0)
        for m in [2, 4, 6, 8, 10, 12]
    ]
    result, _ = find_non_overlapping_combinations({"trip1": trip1_windows, "trip2": trip2_windows}, 100)
    assert len(result) == 20

def test_find_non_overlapping_combinations_returns_highest_scores():
    # top 20: 1×(10,10,10) + 3×(10,10,5) + 3×(10,10,1) + 3×(10,5,5) + 6×mixed-5.33 + 1×(5,5,5) + 3×(10,1,1) = 20
    # bottom 7: all combos averaging < 4.0
    scores = [10.0, 5.0, 1.0]

    def make_windows(trip_id, months):
        return [
            Window(trip_id=trip_id, start_date=datetime.date(2026, m, 1), end_date=datetime.date(2026, m, 5),
                   total_days=5, vacation_days_cost=1, weekend_anchored=False, overlaps_holiday=False, score=s)
            for m, s in zip(months, scores)
        ]

    windows_by_trip = {
        "trip1": make_windows("trip1", [1, 4, 7]),
        "trip2": make_windows("trip2", [2, 5, 8]),
        "trip3": make_windows("trip3", [3, 6, 9]),
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 100)
    assert len(result) == 20
    assert result[0].total_score == 10.0
    assert result[-1].total_score == 4.0
    assert all(plan.total_score >= 4.0 for plan in result)


def test_find_non_overlapping_combinations_empty_list():
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False)],
        "trip2": [],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 5)
    assert len(result) == 0

def test_find_non_overlapping_combinations_all_overlaps():
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False),
                  Window(trip_id="trip1", start_date=datetime.date(2026, 5,6), end_date=datetime.date(2026, 5, 8), total_days=3, vacation_days_cost=3, weekend_anchored=False, overlaps_holiday=False)],
        "trip2": [Window(trip_id="trip2", start_date=datetime.date(2026, 4,30), end_date=datetime.date(2026, 5, 6), total_days=7, vacation_days_cost=5, weekend_anchored=False, overlaps_holiday=False),
                  Window(trip_id="trip2", start_date=datetime.date(2026, 5,2), end_date=datetime.date(2026, 5, 7), total_days=6, vacation_days_cost=4, weekend_anchored=True, overlaps_holiday=False)],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 20)
    assert len(result) == 0

def test_find_non_overlapping_combinations_exact_budget():
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False)],
        "trip2": [Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=5, weekend_anchored=False, overlaps_holiday=False)],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 8)
    assert len(result) == 1
    assert {w.trip_id for w in result[0].windows} == {"trip1", "trip2"}

def test_find_non_overlapping_combinations_multiple_valid():
    # trip1 has 2 windows, trip2 has 2 windows, all 4 are mutually non-overlapping
    # so the function should find 4 valid plan
    windows_by_trip = {
        "trip1": [
            Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False),
            Window(trip_id="trip1", start_date=datetime.date(2026, 7, 1), end_date=datetime.date(2026, 7, 5), total_days=5, vacation_days_cost=3, weekend_anchored=True, overlaps_holiday=False),
        ],
        "trip2": [
            Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=3, weekend_anchored=False, overlaps_holiday=False),
            Window(trip_id="trip2", start_date=datetime.date(2026, 8, 1), end_date=datetime.date(2026, 8, 5), total_days=5, vacation_days_cost=3, weekend_anchored=False, overlaps_holiday=False),
        ],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 20)
    assert len(result) == 4

def test_find_non_overlapping_combinations_three_trips():
    # All three trips are in different months — exactly one valid combination
    windows_by_trip = {
        "trip1": [Window(trip_id="trip1", start_date=datetime.date(2026, 5, 1), end_date=datetime.date(2026, 5, 5), total_days=5, vacation_days_cost=2, weekend_anchored=True, overlaps_holiday=False)],
        "trip2": [Window(trip_id="trip2", start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 5), total_days=5, vacation_days_cost=2, weekend_anchored=False, overlaps_holiday=False)],
        "trip3": [Window(trip_id="trip3", start_date=datetime.date(2026, 7, 1), end_date=datetime.date(2026, 7, 5), total_days=5, vacation_days_cost=2, weekend_anchored=True, overlaps_holiday=False)],
    }
    result, _ = find_non_overlapping_combinations(windows_by_trip, 10)
    assert len(result) == 1
    assert {w.trip_id for w in result[0].windows} == {"trip1", "trip2", "trip3"}

def test_solve_returns_ok_on_valid_input():
    result = solve({
        "vacation_days_remaining": 10,
        "year": 2026,
        "trips": [
            {"id": "trip1", "destination": "Tokyo", "departure_cities": ["NYC"], "min_duration_days": 4},
            {"id": "trip2", "destination": "Chicago", "departure_cities": ["NYC"], "min_duration_days": 4},
        ],
        "blackout_dates": [],
        "earliest_start": "2026-05-01",
        "latest_end": "2026-12-31"
    })
    assert result["status"] == "ok"

def test_solve_returns_error_on_invalid_input():
    result = solve({"vacation_days_remaining": "not a number", "year": 2026, "trips": [], "earliest_start": "2026-05-01", "latest_end": "2026-12-31"})
    assert result["status"] == "error"
    assert "message" in result

def test_solve_end_to_end():
    result = solve({
        "vacation_days_remaining": 10,
        "year": 2026,
        "trips": [
            {"id": "trip_nyc", "destination": "New York City", "departure_cities": ["SFO"], "min_duration_days": 4},
            {"id": "trip_chicago", "destination": "Chicago", "departure_cities": ["SFO"], "min_duration_days": 4},
        ],
        "blackout_dates": [],
        "earliest_start": "2026-05-01",
        "latest_end": "2026-12-31"
    })
    assert result["status"] == "ok"
    assert len(result["combined_plans"]) > 0
    for plan in result["combined_plans"]:
        dates = [(w["start_date"], w["end_date"]) for w in plan["windows"]]
        for i in range(len(dates)):
            for j in range(i + 1, len(dates)):
                assert not (dates[i][0] <= dates[j][1] and dates[j][0] <= dates[i][1])

# agent.py testing
def test_format_solver_error_for_claude_include_error():
    result = solve({"vacation_days_remaining": "not a number", "year": 2026, "trips": [], "earliest_start": "2026-05-01", "latest_end": "2026-12-31"})
    error_message = result["message"]
    formatted = format_solver_error_for_claude(result)
    assert error_message in formatted

def test_format_top_plans_n_plan_available():
    result = {
        "status": "ok",
        "trips": {
            "trip_nyc": [
                {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                },
                {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-6-01",
                    "end_date": "2026-06-05",
                    "vacation_days_cost": 4,
                    "weekend_anchored": False,
                    "overlaps_holiday": False,
                    "score": 0.826452
                }
            ],
            "trip_lax": [
                {
                    "trip_id": "trip_lax",
                    "start_date": "2026-7-01",
                    "end_date": "2026-07-05",
                    "vacation_days_cost": 2,
                    "weekend_anchored": True,
                    "overlaps_holiday": True,
                    "score": 0.96352
                },
                {
                    "trip_id": "trip_lax",
                    "start_date": "2026-8-01",
                    "end_date": "2026-08-05",
                    "vacation_days_cost": 4,
                    "weekend_anchored": False,
                    "overlaps_holiday": False,
                    "score": 0.826452
                }
            ]
        },
        "combined_plans": [
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-6-01",
                    "end_date": "2026-06-05",
                    "vacation_days_cost": 4,
                    "weekend_anchored": False,
                    "overlaps_holiday": False,
                    "score": 0.826452
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-7-01",
                        "end_date": "2026-07-05",
                        "vacation_days_cost": 2,
                        "weekend_anchored": True,
                        "overlaps_holiday": True,
                        "score": 0.96352
                    },
                ],
                "total_vacation_days": 6,
                "total_score": 0.9653
            },
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-8-01",
                        "end_date": "2026-08-05",
                        "vacation_days_cost": 4,
                        "weekend_anchored": False,
                        "overlaps_holiday": False,
                        "score": 0.826452
                    }   
                ],
                "total_vacation_days": 7,
                "total_score": 0.7533
            },
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-7-01",
                        "end_date": "2026-07-05",
                        "vacation_days_cost": 2,
                        "weekend_anchored": True,
                        "overlaps_holiday": True,
                        "score": 0.96352
                    },
                ],
                "total_vacation_days": 5,
                "total_score": 0.9653
            },
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-8-01",
                        "end_date": "2026-08-05",
                        "vacation_days_cost": 4,
                        "weekend_anchored": False,
                        "overlaps_holiday": False,
                        "score": 0.826452
                    } 
                ],
                "total_vacation_days": 7,
                "total_score": 0.77434
            },

        ],
        "metadata": {
                "total_windows_generated": 4,
                "combinations_evaluated": 4,
                "combinations_returned": 4
        }
    }
    formatted = format_top_plans(result, 2)
    assert "Top 2 plans" in formatted
    assert "Plan 1" in formatted
    assert "Plan 2" in formatted
    assert not "Plan 3" in formatted

def test_format_top_plans_fewer_than_n_plan_available():
    result = {
        "status": "ok",
        "trips": {
            "trip_nyc": [
                {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                },
                {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-6-01",
                    "end_date": "2026-06-05",
                    "vacation_days_cost": 4,
                    "weekend_anchored": False,
                    "overlaps_holiday": False,
                    "score": 0.826452
                }
            ],
            "trip_lax": [
                {
                    "trip_id": "trip_lax",
                    "start_date": "2026-7-01",
                    "end_date": "2026-07-05",
                    "vacation_days_cost": 2,
                    "weekend_anchored": True,
                    "overlaps_holiday": True,
                    "score": 0.96352
                },
                {
                    "trip_id": "trip_lax",
                    "start_date": "2026-8-01",
                    "end_date": "2026-08-05",
                    "vacation_days_cost": 4,
                    "weekend_anchored": False,
                    "overlaps_holiday": False,
                    "score": 0.826452
                }
            ]
        },
        "combined_plans": [
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-6-01",
                    "end_date": "2026-06-05",
                    "vacation_days_cost": 4,
                    "weekend_anchored": False,
                    "overlaps_holiday": False,
                    "score": 0.826452
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-7-01",
                        "end_date": "2026-07-05",
                        "vacation_days_cost": 2,
                        "weekend_anchored": True,
                        "overlaps_holiday": True,
                        "score": 0.96352
                    },
                ],
                "total_vacation_days": 6,
                "total_score": 0.9653
            },
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-8-01",
                        "end_date": "2026-08-05",
                        "vacation_days_cost": 4,
                        "weekend_anchored": False,
                        "overlaps_holiday": False,
                        "score": 0.826452
                    }   
                ],
                "total_vacation_days": 7,
                "total_score": 0.7533
            },
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-7-01",
                        "end_date": "2026-07-05",
                        "vacation_days_cost": 2,
                        "weekend_anchored": True,
                        "overlaps_holiday": True,
                        "score": 0.96352
                    },
                ],
                "total_vacation_days": 5,
                "total_score": 0.9653
            },
            {
                "windows": [
                    {
                    "trip_id": "trip_nyc",
                    "start_date": "2026-5-01",
                    "end_date": "2026-05-05",
                    "vacation_days_cost": 3,
                    "weekend_anchored": True,
                    "overlaps_holiday": False,
                    "score": 0.8634523
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-8-01",
                        "end_date": "2026-08-05",
                        "vacation_days_cost": 4,
                        "weekend_anchored": False,
                        "overlaps_holiday": False,
                        "score": 0.826452
                    } 
                ],
                "total_vacation_days": 7,
                "total_score": 0.77434
            },

        ],
        "metadata": {
                "total_windows_generated": 4,
                "combinations_evaluated": 4,
                "combinations_returned": 4
        }
    }
    formatted = format_top_plans(result, 5)
    assert "Top 4 plans" in formatted
    assert "Plan 1" in formatted
    assert "Plan 2" in formatted
    assert "Plan 3" in formatted
    assert "Plan 4" in formatted

def test_format_top_plans_weekend_anchored_marking():
    result = {
        "status": "ok",
        "trips": {},
        "combined_plans": [
            {
                "windows": [
                    {
                        "trip_id": "trip_nyc",
                        "start_date": "2026-05-01",
                        "end_date": "2026-05-05",
                        "vacation_days_cost": 3,
                        "weekend_anchored": True,
                        "overlaps_holiday": False,
                        "score": 0.9
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-06-01",
                        "end_date": "2026-06-05",
                        "vacation_days_cost": 3,
                        "weekend_anchored": False,
                        "overlaps_holiday": False,
                        "score": 0.7
                    }
                ],
                "total_vacation_days": 6,
                "total_score": 0.8
            }
        ],
        "metadata": {
            "total_windows_generated": 2,
            "combinations_evaluated": 1,
            "combinations_returned": 1
        }
    }
    formatted = format_top_plans(result, 1)
    lines = formatted.splitlines()
    nyc_line = next(l for l in lines if "trip_nyc" in l)
    lax_line = next(l for l in lines if "trip_lax" in l)
    assert "[weekend ✓]" in nyc_line
    assert "[weekend x]" in lax_line

def test_format_top_plans_holiday_anchored_marking():
    result = {
        "status": "ok",
        "trips": {},
        "combined_plans": [
            {
                "windows": [
                    {
                        "trip_id": "trip_nyc",
                        "start_date": "2026-05-01",
                        "end_date": "2026-05-05",
                        "vacation_days_cost": 3,
                        "weekend_anchored": True,
                        "overlaps_holiday": True,
                        "score": 0.9
                    },
                    {
                        "trip_id": "trip_lax",
                        "start_date": "2026-06-01",
                        "end_date": "2026-06-05",
                        "vacation_days_cost": 3,
                        "weekend_anchored": False,
                        "overlaps_holiday": False,
                        "score": 0.7
                    }
                ],
                "total_vacation_days": 6,
                "total_score": 0.8
            }
        ],
        "metadata": {
            "total_windows_generated": 2,
            "combinations_evaluated": 1,
            "combinations_returned": 1
        }
    }
    formatted = format_top_plans(result, 1)
    lines = formatted.splitlines()
    nyc_line = next(l for l in lines if "trip_nyc" in l)
    lax_line = next(l for l in lines if "trip_lax" in l)
    assert "[holiday ✓]" in nyc_line
    assert "[holiday x]" in lax_line









