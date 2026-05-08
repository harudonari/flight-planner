"""
Run: python demo.py

Prints a human-readable summary of the top 5 combined plans
for a sample input.
"""
from solver import solve

sample = {
    "vacation_days_remaining": 10,
    "year": 2026,
    "trips": [
        {
            "id": "trip_nyc",
            "destination": "New York City",
            "departure_cities": ["SFO"],
            "min_duration_days": 4
        },
        {
            "id": "trip_chicago",
            "destination": "Chicago",
            "departure_cities": ["SFO"],
            "min_duration_days": 4
        },
        {
            "id": "trip_seattle",
            "destination": "Seattle",
            "departure_cities": ["SFO"],
            "min_duration_days": 4
        }
    ],
    "blackout_dates": [],
    "earliest_start": "2026-05-01",
    "latest_end": "2026-12-31"
}

result = solve(sample)

print(f"Status: {result['status']}")
print(f"Windows generated: {result['metadata']['total_windows_generated']}")
print(f"Combined plans found: {len(result['combined_plans'])}\n")

for i, plan in enumerate(result['combined_plans'][:10], 1):
    print(f"--- Plan {i} (score: {plan['total_score']:.2f}, vacation days: {plan['total_vacation_days']}) ---")
    for w in plan['windows']:
        anchored = "✓ weekend" if w['weekend_anchored'] else "  weekday"
        print(f"  {w['trip_id']:15} {w['start_date']} → {w['end_date']}  [{anchored}]  cost: {w['vacation_days_cost']}d")
    print()