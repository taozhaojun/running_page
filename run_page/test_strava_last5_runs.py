import argparse
from datetime import datetime, timezone

import stravalib


def fetch_last_5_runs(client_id: str, client_secret: str, refresh_token: str) -> list:
    client = stravalib.Client()
    token_response = client.refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )
    client.access_token = token_response["access_token"]

    activities = client.get_activities(before=datetime.now(timezone.utc), limit=100)
    runs = []
    for activity in activities:
        if activity.type == "Run":
            runs.append(activity)
        if len(runs) >= 5:
            break
    return runs


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and print last 5 running activities from Strava."
    )
    parser.add_argument("client_id", help="Strava client id")
    parser.add_argument("client_secret", help="Strava client secret")
    parser.add_argument("refresh_token", help="Strava refresh token")
    args = parser.parse_args()

    runs = fetch_last_5_runs(args.client_id, args.client_secret, args.refresh_token)
    if not runs:
        print("No running activities found.")
        return

    print(f"Found {len(runs)} latest running activities:")
    for idx, run in enumerate(runs, start=1):
        distance_km = float(run.distance) / 1000 if run.distance is not None else 0.0
        print(
            f"{idx}. id={run.id} | name={run.name} | "
            f"start_local={run.start_date_local} | type={run.type} | "
            f"distance_km={distance_km:.2f}"
        )


if __name__ == "__main__":
    main()
