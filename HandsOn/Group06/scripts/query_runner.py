"""
SPARQL Query Runner for Madrid Bus Network RDF Data

This script validates the RDF transformation using LightRDF streaming.
No memory load required - handles large (5GB+) RDF files efficiently.

Usage:
    python3 query_runner.py           # Run on base RDF dataset
    python3 query_runner.py --links   # Run on RDF dataset with Wikidata links
"""

import argparse
import time
from pathlib import Path

import pandas as pd

# Require LightRDF for streaming
try:
    import lightrdf
except ImportError:
    print("ERROR: LightRDF is required for this script.")
    print("Install with: pip install lightrdf")
    exit(1)


def load_csv_stats(data_dir):
    """Load and compute statistics from CSV files"""
    print(f"\n{'=' * 70}")
    print("Loading CSV Statistics")
    print(f"{'=' * 70}")

    stats = {}

    try:
        df_final = pd.read_csv(data_dir / "df_final-updated.csv", low_memory=False)
        stats["routes"] = df_final["route_id"].nunique()
        stats["stops"] = df_final["stop_id"].nunique()
        stats["trips"] = df_final["trip_id"].nunique()
        stats["services"] = df_final["service_id"].nunique()
        stats["shapes"] = (
            df_final["shape_id"].nunique() if "shape_id" in df_final.columns else 0
        )
        stats["stop_times"] = len(df_final)

        df_areas = pd.read_csv(data_dir / "local_areas-updated.csv")
        stats["local_areas"] = len(df_areas)

        df_calendar = pd.read_csv(data_dir / "calendar-updated.csv")
        stats["calendar_rules"] = len(df_calendar)

        df_calendar_dates = pd.read_csv(data_dir / "calendar_dates-updated.csv")
        stats["calendar_dates"] = len(df_calendar_dates)

        df_shapes = pd.read_csv(data_dir / "shapes-updated.csv")
        stats["shape_points"] = len(df_shapes)

        print(f"\nCSV Summary:")
        print(f"  Routes:        {stats['routes']:>10,}")
        print(f"  Stops:         {stats['stops']:>10,}")
        print(f"  Trips:         {stats['trips']:>10,}")
        print(f"  Stop Times:    {stats['stop_times']:>10,}")
        print(f"  Local Areas:   {stats['local_areas']:>10,}")
        print(f"  Services:      {stats['services']:>10,}")
        print(f"  Shapes:        {stats['shapes']:>10,}")
        print(f"  Shape Points:  {stats['shape_points']:>10,}")

        return stats

    except Exception as e:
        print(f"  ✗ Error loading CSV stats: {e}")
        return {}


def get_rdf_stats_streaming(rdf_file):
    """Compute statistics from RDF data using streaming (no memory load)"""
    print(f"\n{'=' * 70}")
    print("Computing RDF Statistics (Streaming)")
    print(f"{'=' * 70}")

    stats = {}
    type_counts = {}
    total_triples = 0

    rdf_type_uris = [
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
    ]

    print("\n⏳ Processing RDF file...")
    start = time.time()

    try:
        doc = lightrdf.RDFDocument(str(rdf_file))

        for triple in doc.search_triples(None, None, None):
            total_triples += 1

            predicate = str(triple[1])
            if predicate in rdf_type_uris or predicate.endswith("#type"):
                type_uri = str(triple[2]).strip("<>")
                type_counts[type_uri] = type_counts.get(type_uri, 0) + 1

            # Progress indicator every 5M triples
            if total_triples % 5000000 == 0:
                print(f"  {total_triples:,} triples...")

        elapsed = time.time() - start
        print(f"✓ Processed {total_triples:,} triples in {elapsed:.2f}s")

    except Exception as e:
        print(f"✗ Error: {e}")
        return {}

    # Display results
    print("\nRDF Resource Counts:")
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    for type_uri, count in sorted_types:
        if "madridbus/" in type_uri:
            class_name = type_uri.split("madridbus/")[-1]
        elif "gtfs.org/terms#" in type_uri:
            class_name = "gtfs:" + type_uri.split("#")[-1]
        else:
            class_name = type_uri.split("/")[-1].split("#")[-1]

        print(f"  {class_name:25} {count:>10,}")

        # Map to stats dictionary
        if "BusRoute" in type_uri:
            stats["routes"] = count
        elif "BusStop" in type_uri:
            stats["stops"] = count
        elif "Trip" in type_uri:
            stats["trips"] = count
        elif "StopTime" in type_uri:
            stats["stop_times"] = count
        elif "LocalArea" in type_uri:
            stats["local_areas"] = count
        elif "Service" in type_uri:
            stats["services"] = count
        elif "CalendarRule" in type_uri:
            stats["calendar_rules"] = count
        elif "CalendarDateRule" in type_uri:
            stats["calendar_dates"] = count
        elif "Shape" in type_uri and "ShapePoint" not in type_uri:
            stats["shapes"] = count
        elif "ShapePoint" in type_uri:
            stats["shape_points"] = count

    return stats


def compare_stats(csv_stats, rdf_stats):
    """Compare CSV and RDF statistics"""
    print(f"\n{'=' * 70}")
    print("CSV vs RDF Comparison")
    print(f"{'=' * 70}")

    metrics = [
        ("Routes", "routes"),
        ("Stops", "stops"),
        ("Trips", "trips"),
        ("Stop Times", "stop_times"),
        ("Local Areas", "local_areas"),
        ("Services", "services"),
        ("Calendar Rules", "calendar_rules"),
        ("Calendar Dates", "calendar_dates"),
        ("Shapes", "shapes"),
        ("Shape Points", "shape_points"),
    ]

    print(f"{'Metric':<20} {'CSV':<12} {'RDF':<12} {'Status':<10}")
    print("-" * 60)

    all_match = True

    for label, key in metrics:
        csv_val = csv_stats.get(key, 0)
        rdf_val = rdf_stats.get(key, 0)

        if csv_val == rdf_val:
            status = "✓ MATCH"
        else:
            status = "✗ DIFFER"
            all_match = False

        print(f"{label:<20} {csv_val:<12,} {rdf_val:<12,} {status:<10}")

    print("-" * 60)

    if all_match:
        print("✓ All metrics match! Data transformation is correct.")
    else:
        print("⚠ Some metrics differ. Review the transformation process.")

    return all_match


def run_simple_query(rdf_file, query_dict, query_num):
    """Execute simple SPARQL query using LightRDF streaming."""
    comment = query_dict["comment"]
    query = query_dict["query"]

    print(f"\n{'=' * 70}")
    print(f"QUERY {query_num}: {comment}")
    print(f"{'=' * 70}")

    import re

    where_match = re.search(r"WHERE\s*\{([^}]+)\}", query, re.DOTALL | re.IGNORECASE)
    if not where_match:
        print("⚠ Could not parse query")
        return

    where_clause = where_match.group(1).strip()
    limit_match = re.search(r"LIMIT\s+(\d+)", query, re.IGNORECASE)
    limit = int(limit_match.group(1)) if limit_match else None

    start = time.time()

    try:
        doc = lightrdf.RDFDocument(str(rdf_file))
        matches = []
        triple_count = 0

        # Handle: ?var rdf:type ex:Class patterns
        type_pattern = re.search(r"\?(\w+)\s+(?:a|rdf:type)\s+(\S+)", where_clause)
        if type_pattern:
            class_uri = type_pattern.group(2)

            # Resolve prefix
            if "ex:" in class_uri:
                class_uri = (
                    "http://group06.linkeddata.es/ontology/madridbus/"
                    + class_uri.split(":")[-1]
                )
            elif "gtfs:" in class_uri:
                class_uri = "http://vocab.gtfs.org/terms#" + class_uri.split(":")[-1]

            for s, p, o in doc.search_triples(None, None, None):
                triple_count += 1
                if "type" in str(p) and class_uri in str(o):
                    matches.append(str(s))
                    if limit and len(matches) >= limit:
                        break

        # Handle: ?var owl:sameAs ?other patterns
        elif "owl:sameAs" in where_clause or "sameAs" in where_clause:
            for s, p, o in doc.search_triples(None, None, None):
                triple_count += 1
                if "sameAs" in str(p):
                    matches.append((str(s), str(o)))
                    if limit and len(matches) >= limit:
                        break

        else:
            print("⚠ Complex query - not supported by streaming")
            return

        elapsed = time.time() - start
        print(f"✓ Completed in {elapsed:.2f}s - Found {len(matches):,} results")

        # Display sample results
        if matches and len(matches) <= 10:
            print("\nResults:")
            for i, match in enumerate(matches, 1):
                if isinstance(match, tuple):
                    print(f"  {i}. {match[0][:65]}... → {match[1][:55]}...")
                else:
                    print(f"  {i}. {match[:75]}...")

    except Exception as e:
        print(f"✗ Error: {str(e)}")


def parse_queries(sparql_file):
    """Parse SPARQL file and extract queries"""
    queries = []
    prefixes = []
    current_query = []
    current_comment = []
    in_prefix_section = True

    with open(sparql_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()

            if not line:
                continue

            # Collect PREFIX declarations
            if line.startswith("PREFIX"):
                if in_prefix_section:
                    prefixes.append(line)
                continue

            # End of prefix section
            if in_prefix_section and line.startswith("#") and "=" in line:
                in_prefix_section = False

            if in_prefix_section:
                continue

            # Query separator
            if line.startswith("#") and "=" in line:
                if current_query:
                    query_text = "\n".join(prefixes + current_query)
                    comment_text = " ".join(current_comment)
                    queries.append({"comment": comment_text, "query": query_text})
                    current_query = []
                    current_comment = []
                continue

            # Comment lines
            if line.startswith("#"):
                comment_line = line.lstrip("#").strip()
                if comment_line:
                    current_comment.append(comment_line)
                continue

            # Query content
            if line:
                current_query.append(line)

        # Save last query
        if current_query:
            query_text = "\n".join(prefixes + current_query)
            comment_text = " ".join(current_comment)
            queries.append({"comment": comment_text, "query": query_text})

    return queries


def main():
    """Main execution"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Validate Madrid Bus Network RDF data using SPARQL queries"
    )
    parser.add_argument(
        "--links",
        action="store_true",
        help="Use RDF dataset with Wikidata links and corresponding queries",
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("RDF Data Validator - Madrid Bus Network")
    if args.links:
        print("Mode: WITH Wikidata Links")
    else:
        print("Mode: Base Dataset (no external links)")
    print("Using LightRDF Streaming (No Memory Load)")
    print("=" * 70)

    # Setup paths
    base_dir = Path(__file__).parent.parent
    rdf_dir = base_dir / "rdf"
    data_dir = base_dir / "data" / "processed"

    # Select appropriate files based on --links flag
    if args.links:
        rdf_file = rdf_dir / "madrid-bus-data-with-links.nt"
        if not rdf_file.exists():
            rdf_file = rdf_dir / "madrid-bus-data-with-links.ttl"
        sparql_file = rdf_dir / "queries-with-links.sparql"
    else:
        rdf_file = rdf_dir / "madrid-bus-data.nt"
        if not rdf_file.exists():
            rdf_file = rdf_dir / "madrid-bus-data.ttl"
        sparql_file = rdf_dir / "queries.sparql"

    # Check files
    if not rdf_file.exists():
        print(f"\n✗ ERROR: RDF file not found: {rdf_file}")
        if args.links:
            print("  Run Morph-KGC with madrid-bus-rml-with-links.rml mapping first.")
            print("  Update configuration.ini to use the with-links mapping.")
        else:
            print("  Run Morph-KGC first to generate the RDF data.")
        return

    if not sparql_file.exists():
        print(f"\n✗ ERROR: SPARQL file not found: {sparql_file}")
        return

    file_size_gb = rdf_file.stat().st_size / (1024**3)
    print(f"\nRDF file: {rdf_file.name} ({file_size_gb:.2f} GB)")

    # Load CSV statistics
    csv_stats = load_csv_stats(data_dir)

    # Get RDF statistics (streaming, no memory load)
    rdf_stats = get_rdf_stats_streaming(rdf_file)

    # Compare
    all_match = False
    if csv_stats and rdf_stats:
        all_match = compare_stats(csv_stats, rdf_stats)

    # Run validation queries
    print(f"\n{'=' * 70}")
    print(f"Running Validation Queries")
    print(f"{'=' * 70}")

    queries = parse_queries(sparql_file)
    print(f"Found {len(queries)} queries\n")

    # Run all queries
    for i, query_dict in enumerate(queries, 1):
        run_simple_query(rdf_file, query_dict, i)

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    if args.links:
        print(f"✓ Mode: WITH Wikidata Links")
    else:
        print(f"✓ Mode: Base Dataset")
    print(f"✓ RDF file: {rdf_file.name} ({file_size_gb:.2f} GB)")
    print(f"✓ Method: LightRDF streaming (no memory load)")
    print(f"✓ Queries executed: {len(queries)}")
    if csv_stats and rdf_stats and all_match:
        print(f"✓ Result: All metrics match CSV data!")
    elif csv_stats and rdf_stats:
        print(f"⚠ Result: Some metrics differ from CSV")
    print("=" * 70)


if __name__ == "__main__":
    main()
