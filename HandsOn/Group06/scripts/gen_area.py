#!/usr/bin/env python3
"""
Script to generate local area information from coordinates.
Reads stop coordinates from df_final-updated.csv and generates
area_id, area_name, and area_code (postal code) for local_areas-updated.csv
"""

import ssl
import time
from pathlib import Path

import certifi
import pandas as pd
from geopy.adapters import BaseSyncAdapter
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

# Configure paths
from pathlib import Path

# Adjust the file paths to match the user's structure
SCRIPT_DIR = Path('/HandsOn/Group06/scripts')
CSV_DIR = SCRIPT_DIR.parent / 'csv'
INPUT_CSV = CSV_DIR / 'df_final-updated.csv'
OUTPUT_CSV = CSV_DIR / 'local_areas-updated.csv'


ctx = ssl.create_default_context(cafile=certifi.where())

geolocator = Nominatim(
    user_agent="group06_area_generator",
    ssl_context=ctx
)

def get_location_info(lat, lon):
    """
    Get location information from coordinates using reverse geocoding.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        tuple: (area_name, postal_code) or (None, None) if not found
    """
    try:
        location = geolocator.reverse((lat, lon), language="es", addressdetails=True)

        if location and location.raw.get("address"):
            address = location.raw["address"]

            # Try to extract area name (suburb, neighbourhood, town, city, etc.)
            area_name = (
                address.get("suburb")
                or address.get("neighbourhood")
                or address.get("town")
                or address.get("city")
                or address.get("municipality")
                or address.get("village")
                or "Unknown"
            )

            # Extract postal code
            postal_code = address.get("postcode", "Unknown")

            return area_name, postal_code
        else:
            return "Unknown", "Unknown"

    except Exception as e:
        print(f"Error geocoding ({lat}, {lon}): {e}")
        return "Unknown", "Unknown"


def main():
    """Main function to process coordinates and generate local areas CSV."""

    print("=" * 60)
    print("Local Area Generator")
    print("=" * 60)

    # Read input CSV
    print(f"\nReading input file: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)

    print(f"Total rows in input: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Extract unique stop locations
    unique_stops = df[["stop_id", "stop_name", "stop_lat", "stop_lon"]].drop_duplicates(
        subset=["stop_id"]
    )
    print(f"\nUnique stops found: {len(unique_stops)}")

    # Prepare results list
    results = []

    # Process each unique stop
    print("\nProcessing locations (this may take a while due to rate limiting)...")
    for idx, row in unique_stops.iterrows():
        stop_id = row["stop_id"]
        stop_name = row["stop_name"]
        lat = row["stop_lat"]
        lon = row["stop_lon"]

        print(
            f"  [{idx + 1}/{len(unique_stops)}] Processing {stop_id} - {stop_name}..."
        )

        # Get location info
        area_name, postal_code = get_location_info(lat, lon)

        results.append(
            {"area_id": stop_id, "area_name": area_name, "area_code": postal_code}
        )

        print(f"    -> Area: {area_name}, Postal Code: {postal_code}")

    # Create DataFrame
    areas_df = pd.DataFrame(results)

    # Remove duplicates based on area_id (stop_id)
    print(f"\nRemoving duplicates...")
    areas_df = areas_df.drop_duplicates(subset=["area_id"], keep="first")
    print(f"Final unique areas: {len(areas_df)}")

    # Save to CSV
    print(f"\nSaving results to: {OUTPUT_CSV}")
    areas_df.to_csv(OUTPUT_CSV, index=False)

    # Display summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total unique areas: {len(areas_df)}")
    print(f"Unique area names: {areas_df['area_name'].nunique()}")
    print(f"Unique postal codes: {areas_df['area_code'].nunique()}")
    print("\nTop 5 areas by frequency:")
    print(areas_df["area_name"].value_counts().head())
    print("\nTop 5 postal codes by frequency:")
    print(areas_df["area_code"].value_counts().head())
    print("\nFirst few rows of output:")
    print(areas_df.head(10))
    print("\n✓ Complete!")


if __name__ == "__main__":
    main()