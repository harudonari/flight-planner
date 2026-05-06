import datetime
from dataclasses import dataclass
from typing import Any

@dataclass
class TripConstraint:
    id: str
    destination: str
    departure_cities: list[str]
    min_duration_days: int

@dataclass
class SolverConstraints:
    vacation_days_remaining: int
    year: int
    trips: list[TripConstraint]
    blackout_dates: set[datetime.date]
    earliest_start: datetime.date
    latest_end: datetime.date
    max_trips: int | None

def _require(raw: dict[str, Any], field: str) -> Any:
    if field not in raw:
        raise ValueError(f"Missing required field: {field}")
    return raw[field]

def parse_constraints(raw: dict) -> SolverConstraints:
    """Parse and validate the raw input dict. Raises ValueError for any missing or invalid field."""
    vacation_days_remaining = _require(raw, 'vacation_days_remaining')
    if not isinstance(vacation_days_remaining, int) or isinstance(vacation_days_remaining, bool) or vacation_days_remaining < 0:
        raise ValueError("vacation_days_remaining must be a non-negative integer")

    year = _require(raw, 'year')
    if not isinstance(year, int) or isinstance(vacation_days_remaining, bool) or not 1900 < year < datetime.datetime.now().year + 10:
        raise ValueError("year must be a valid year between 1900 and 10 years from now")

    trips_raw = _require(raw, 'trips')
    if not isinstance(trips_raw, list) or not trips_raw:
        raise ValueError("trips must be a list of trip constraints")

    trips = []
    seen_ids = set()
    for trip_raw in trips_raw:
        trip_id = _require(trip_raw, 'id')
        if trip_id in seen_ids:
            raise ValueError(f"Duplicate trip id: {trip_id}")
        seen_ids.add(trip_id)

        destination = _require(trip_raw, 'destination')
        if not destination:
            raise ValueError(f"Trip {trip_id} has an empty destination")

        departure_cities = _require(trip_raw, 'departure_cities')
        if not isinstance(departure_cities, list) or not departure_cities:
            raise ValueError(f"Trip {trip_id} must have a non-empty list of departure cities")

        min_duration_days = _require(trip_raw, 'min_duration_days')
        if not isinstance(min_duration_days, int) or isinstance(vacation_days_remaining, bool) or min_duration_days <= 0:
            raise ValueError(f"Trip {trip_id} must have a positive integer min_duration_days")

        trips.append(TripConstraint(id=trip_id, destination=destination, departure_cities=departure_cities, min_duration_days=min_duration_days))

    # Optional — no blackout dates is a valid state
    blackout_dates_raw = raw.get('blackout_dates', [])
    if not isinstance(blackout_dates_raw, list):
        raise ValueError("blackout_dates must be a list of date strings in YYYY-MM-DD format")
    blackout_dates = set()
    for date_str in blackout_dates_raw:
        try:
            blackout_dates.add(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            raise ValueError(f"Invalid date format for blackout_date '{date_str}': expected YYYY-MM-DD")

    earliest_start_str = _require(raw, 'earliest_start')
    try:
        earliest_start = datetime.datetime.strptime(earliest_start_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format for earliest_start '{earliest_start_str}': expected YYYY-MM-DD")

    latest_end_str = _require(raw, 'latest_end')
    try:
        latest_end = datetime.datetime.strptime(latest_end_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format for latest_end '{latest_end_str}': expected YYYY-MM-DD")

    if earliest_start >= latest_end:
        raise ValueError("earliest_start must be before latest_end")

    max_trips = raw.get('max_trips')
    if max_trips is not None:
        if not isinstance(max_trips, int) or isinstance(vacation_days_remaining, bool) or max_trips <= 0:
            raise ValueError("max_trips must be a positive integer if provided")

    return SolverConstraints(
        vacation_days_remaining=vacation_days_remaining,
        year=year,
        trips=trips,
        blackout_dates=blackout_dates,
        earliest_start=earliest_start,
        latest_end=latest_end,
        max_trips=max_trips,
    )

def is_weekend(date: datetime.date) -> bool:
    """Return True if date falls on Saturday or Sunday."""
    return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday

def _observed(date: datetime.date) -> datetime.date:
    """Helper function for calculating observed holidays when it falls onto weekends."""
    if date.weekday() == 5: # Saturday
        return date - datetime.timedelta(days=1) # Observed on Friday
    if date.weekday() == 6: # Sunday
        return date + datetime.timedelta(days=1) # Observed on Monday
    return date

def get_us_federal_holidays(year: int) -> set[datetime.date]:
    """Return a set of US federal public holiday dates for the given year.
    Hardcode the 11 federal holidays. Account for observed dates
    (e.g. if July 4 falls on Sunday, observed Monday is the holiday)."""
    holidays = set()
    # New Year's Day (January 1st)
    new_years_day = _observed(datetime.date(year, 1, 1))
    holidays.add(new_years_day)
    # Martin Luther King, Jr. Day (3rd Monday in January)
    mlk_day = datetime.date(year, 1, 1) + datetime.timedelta(days=(7 - datetime.date(year, 1, 1).weekday()) % 7 + 14)
    holidays.add(mlk_day)
    # President's Day (3rd Monday in February)
    presidents_day = datetime.date(year, 2, 1) + datetime.timedelta(days=(7 - datetime.date(year, 2, 1).weekday()) % 7 + 14)
    holidays.add(presidents_day)
    # Memorial Day (last Monday in May)
    memorial_day = datetime.date(year, 5, 31) - datetime.timedelta(days=datetime.date(year, 5, 31).weekday())
    holidays.add(memorial_day)
    # Juneteenth National Independence Day (June 19)
    juneteenth = _observed(datetime.date(year, 6, 19))
    holidays.add(juneteenth)
    # Independence Day (July 4)
    independence_day = _observed(datetime.date(year, 7, 4))
    holidays.add(independence_day)
    # Labor Day (1st Monday in September)
    labor_day = datetime.date(year, 9, 1) + datetime.timedelta(days=(7 - datetime.date(year, 9, 1).weekday()) % 7)
    holidays.add(labor_day)
    # Columbus Day (2nd Monday in October)
    columbus_day = datetime.date(year, 10, 1) + datetime.timedelta(days=(7 - datetime.date(year, 10, 1).weekday()) % 7 + 7)
    holidays.add(columbus_day)
    # Veterans Day (November 11)
    veterans_day = _observed(datetime.date(year, 11, 11))
    holidays.add(veterans_day)
    # Thanksgiving (4th Thursday in November)
    thanksgiving = datetime.date(year, 11, 1) + datetime.timedelta(days=(3 - datetime.date(year, 11, 1).weekday()) % 7 + 21)
    holidays.add(thanksgiving)
    # Christmas (December 25)
    christmas = _observed(datetime.date(year, 12, 25))
    holidays.add(christmas)

    return holidays

def is_vacation_day(date: datetime.date, holidays: set[datetime.date]) -> bool:
    """Return True if date costs a vacation day
    (i.e. it is a weekday and not a federal holiday)."""
    return not is_weekend(date) and date not in holidays

def count_vacation_days(start: datetime.date, end: datetime.date, holidays: set[datetime.date]) -> int:
    """Count how many vacation days are consumed between start and end (inclusive).
    Weekends and holidays are free."""
    vacation_days = 0
    current_date = start
    while current_date <= end:
        if is_vacation_day(current_date, holidays):
            vacation_days += 1
        current_date += datetime.timedelta(days=1)
    return vacation_days