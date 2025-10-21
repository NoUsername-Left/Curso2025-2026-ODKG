"""
GTFS Madrid Dataset Preprocessing Script for Assignment 2

Prepares the Madrid CRTM GTFS dataset for RDF transformation:
1. Converts .txt files to .csv
2. Creates merged dataset
3. Adds service_id for schedule filtering
4. Processes calendar data for date filtering

Output: data/processed/ directory with clean CSV files ready for RDF transformation
"""

from pathlib import Path

import pandas as pd


def convert_txt_to_csv(source_dir, output_dir, gtfs_files):
    """
    Convert GTFS .txt files to .csv format

    Parameters:
    - source_dir: Path to directory with .txt files
    - output_dir: Path to output directory
    - gtfs_files: List of file names

    Returns:
    - Dict with file statistics
    """
    print("\n" + "=" * 70)
    print("STEP 1: CONVERTING .txt TO .csv")
    print("=" * 70)

    output_dir.mkdir(exist_ok=True)
    stats = {}

    for file_name in gtfs_files:
        source_file = source_dir / f"{file_name}.txt"
        output_file = output_dir / f"{file_name}.csv"

        try:
            df = pd.read_csv(source_file)
            df.to_csv(output_file, index=False)

            stats[file_name] = {"records": len(df), "columns": len(df.columns)}
            print(f"✓ {file_name:20} | {len(df):>10,} rows | {len(df.columns):>2} cols")

        except Exception as e:
            print(f"✗ {file_name:20} | ERROR: {e}")
            stats[file_name] = {"records": 0, "columns": 0, "error": str(e)}

    return stats


def verify_data_integrity(output_dir):
    """
    Verify referential integrity of GTFS data

    Parameters:
    - output_dir: Path to directory with CSV files

    Returns:
    - Tuple of (routes, trips, stops, stop_times) dataframes
    """
    print("\n" + "=" * 70)
    print("STEP 2: VERIFYING DATA INTEGRITY")
    print("=" * 70)

    routes = pd.read_csv(output_dir / "routes.csv")
    trips = pd.read_csv(output_dir / "trips.csv")
    stops = pd.read_csv(output_dir / "stops.csv")
    stop_times = pd.read_csv(output_dir / "stop_times.csv")

    print(f"\nRecord counts:")
    print(f"  Routes:      {len(routes):>10,}")
    print(f"  Trips:       {len(trips):>10,}")
    print(f"  Stops:       {len(stops):>10,}")
    print(f"  Stop-times:  {len(stop_times):>10,}")

    # Check referential integrity
    trips_valid = trips["route_id"].isin(routes["route_id"]).sum()
    stop_times_trips_valid = stop_times["trip_id"].isin(trips["trip_id"]).sum()
    stop_times_stops_valid = stop_times["stop_id"].isin(stops["stop_id"]).sum()

    print(f"\nReferential integrity:")
    print(f"  Trips with valid route_id:     {trips_valid:>10,} / {len(trips):>10,}")
    print(
        f"  Stop-times with valid trip_id: {stop_times_trips_valid:>10,} / {len(stop_times):>10,}"
    )
    print(
        f"  Stop-times with valid stop_id: {stop_times_stops_valid:>10,} / {len(stop_times):>10,}"
    )

    all_valid = (
        trips_valid == len(trips)
        and stop_times_trips_valid == len(stop_times)
        and stop_times_stops_valid == len(stop_times)
    )

    if all_valid:
        print("\n✅ All relationships valid")
    else:
        print("\n⚠️  Integrity issues detected")

    return routes, trips, stops, stop_times


def create_merged_dataset(routes, trips, stops, stop_times, output_dir):
    """
    Create merged dataset: routes → trips → stop_times → stops

    Parameters:
    - routes, trips, stops, stop_times: DataFrames
    - output_dir: Path to output directory

    Returns:
    - Merged DataFrame with service_id added
    """
    print("\n" + "=" * 70)
    print("STEP 3: CREATING MERGED DATASET + ADDING SERVICE_ID")
    print("=" * 70)

    # Step 1: Merge routes with trips
    df = trips.merge(routes, on="route_id", how="left")
    print(f"  After routes+trips:     {len(df):>10,} rows")

    # Step 2: Merge with stop_times (this is where we get 1.75M records)
    df = df.merge(stop_times, on="trip_id", how="left")
    print(f"  After +stop_times:      {len(df):>10,} rows")

    # Step 3: Merge with stops
    df = df.merge(stops, on="stop_id", how="left")
    print(f"  After +stops:           {len(df):>10,} rows")

    # Keep essential columns for RDF transformation
    essential_cols = [
        # Trip identifiers
        "trip_id",
        "route_id",
        "service_id",  # ← Added from trips
        "trip_headsign",
        "direction_id",
        "shape_id",  # ← Added from trips (for optional route visualization)
        # Route information
        "route_short_name",
        "route_long_name",
        "route_type",
        # Stop information
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
        # Timing
        "arrival_time",
        "departure_time",
        "stop_sequence",
        # Accessibility
        "wheelchair_boarding",
    ]

    # Keep only columns that exist
    available_cols = [col for col in essential_cols if col in df.columns]
    df_final = df[available_cols].copy()

    print(
        f"\nFinal dataset:          {len(df_final):>10,} rows × {len(df_final.columns)} columns"
    )
    print(f"Columns: {df_final.columns.tolist()}")

    # Check if service_id was added
    if "service_id" in df_final.columns:
        missing_service = df_final["service_id"].isnull().sum()
        print(f"\n✓ service_id added (missing: {missing_service:,})")
    else:
        print("\n⚠️  service_id not found in trips.csv")

    # Save
    output_file = output_dir / "df_final.csv"
    df_final.to_csv(output_file, index=False)
    print(f"\n✓ Saved to: {output_file}")

    return df_final


def process_calendar_data(output_dir):
    """
    Verify calendar data is available

    Parameters:
    - output_dir: Path to directory with CSV files

    Returns:
    - Tuple of (calendar, calendar_dates) dataframes
    """
    print("\n" + "=" * 70)
    print("STEP 4: VERIFYING CALENDAR DATA")
    print("=" * 70)

    calendar_file = output_dir / "calendar.csv"
    calendar_dates_file = output_dir / "calendar_dates.csv"

    calendar = pd.read_csv(calendar_file)
    calendar_dates = pd.read_csv(calendar_dates_file)

    print(f"\nCalendar data:")
    print(f"  calendar.csv:       {len(calendar):>10,} service patterns")
    print(f"  calendar_dates.csv: {len(calendar_dates):>10,} date exceptions")

    # Show sample
    print(f"\nCalendar columns: {calendar.columns.tolist()}")
    print(f"Sample service_ids: {calendar['service_id'].head(3).tolist()}")

    return calendar, calendar_dates


def print_summary(df_final, calendar, calendar_dates, shapes):
    """Print final summary statistics, columns and schema, and required CSVs for the app"""
    print("\n" + "=" * 70)
    print("PREPROCESSING COMPLETE - SUMMARY")
    print("=" * 70)

    print(f"\n✅ Main dataset (df_final.csv):")
    print(f"   - Records:        {len(df_final):>10,}")
    print(f"   - Columns:        {len(df_final.columns):>10,}")
    print(f"   - Routes:         {df_final['route_id'].nunique():>10,}")
    print(f"   - Trips:          {df_final['trip_id'].nunique():>10,}")
    print(f"   - Stops:          {df_final['stop_id'].nunique():>10,}")
    print(f"   - Services:       {df_final['service_id'].nunique():>10,}")

    print("\n🔎 Columns in merged dataset:")
    print("   ", df_final.columns.tolist())

    print("\n🔎 Data types (schema):")
    print(df_final.dtypes.apply(lambda x: x.name))

    print("\n✅ Application-required CSV files:")
    print(f"   - df_final.csv   (main merged GTFS dataset for queries)")
    print(
        f"   - calendar.csv              (service patterns/rules: {len(calendar):,} rows)"
    )
    print(
        f"   - calendar_dates.csv        (date-specific exceptions: {len(calendar_dates):,} rows)"
    )
    print(f"   - shapes.csv                (route geometries: {len(shapes):,} shapes)")

    # Optionally show sample columns from required files
    print("\nSample columns:")
    print(f"   calendar.csv:        {calendar.columns.tolist()}")
    print(f"   calendar_dates.csv:  {calendar_dates.columns.tolist()}")
    print(f"   shapes.csv:          {shapes.columns.tolist()}")

    print(f"\n🚀 Ready for RDF transformation!")
    print("=" * 70)


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("GTFS MADRID DATASET PREPROCESSING")
    print("=" * 70)

    # Setup paths
    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / "data/raw"
    output_dir = base_dir / "data/processed"

    print(f"\nSource: {source_dir}")
    print(f"Output: {output_dir}")

    # GTFS files to process
    gtfs_files = [
        "agency",
        "routes",
        "trips",
        "stops",
        "stop_times",
        "calendar",
        "calendar_dates",
        "shapes",
    ]

    # Step 1: Convert .txt to .csv
    stats = convert_txt_to_csv(source_dir, output_dir, gtfs_files)

    # Step 2: Verify data integrity
    routes, trips, stops, stop_times = verify_data_integrity(output_dir)

    # Step 3: Create merged dataset (includes service_id from trips)
    df_final = create_merged_dataset(routes, trips, stops, stop_times, output_dir)

    # Step 4: Verify calendar data
    calendar, calendar_dates = process_calendar_data(output_dir)

    # Load shapes for summary
    shapes = pd.read_csv(output_dir / "shapes.csv")

    # Summary
    print_summary(df_final, calendar, calendar_dates, shapes)


if __name__ == "__main__":
    main()
