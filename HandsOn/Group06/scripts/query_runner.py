"""
SPARQL Query Runner for Madrid Bus Network RDF Data

This script loads the generated RDF data and executes SPARQL queries from queries.sparql
to verify the data transformation.

Usage:
    python3 query_runner.py
"""

import time
from pathlib import Path

from rdflib import Graph


def load_rdf_data(rdf_file):
    """Load RDF data from N-Triples file"""
    print(f"\n{'=' * 70}")
    print(f"Loading RDF data from: {rdf_file.name}")
    print(f"{'=' * 70}")

    g = Graph()
    start = time.time()

    # Parse N-Triples format
    g.parse(rdf_file, format="nt")

    elapsed = time.time() - start
    print(f"✓ Loaded {len(g):,} triples in {elapsed:.2f} seconds")

    return g


def parse_sparql_file(sparql_file):
    """Parse SPARQL file and extract individual queries"""
    queries = []
    prefixes = []
    current_query = []
    current_comment = []
    in_query = False
    in_prefix_section = True  # Start in prefix section

    with open(sparql_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()

            # Skip empty lines outside queries
            if not line and not in_query:
                continue

            # Collect PREFIX declarations at the beginning (after initial comments)
            if line.startswith("PREFIX"):
                if in_prefix_section:
                    prefixes.append(line)
                    continue

            # Once we hit a separator line after prefixes, prefix section is done
            if in_prefix_section and line.startswith("#") and "=" in line:
                in_prefix_section = False

            # Detect comment lines (query descriptions)
            if line.startswith("#"):
                if "=" in line:  # Section separator
                    if current_query:
                        # Prepend prefixes to each query
                        full_query = "\n".join(prefixes + [""] + current_query)
                        queries.append(
                            {
                                "comment": "\n".join(current_comment),
                                "query": full_query,
                            }
                        )
                        current_query = []
                        current_comment = []
                        in_query = False
                else:
                    current_comment.append(line)
            # Detect query start (SELECT, ASK, CONSTRUCT, DESCRIBE)
            elif (
                line.startswith("SELECT")
                or line.startswith("ASK")
                or line.startswith("CONSTRUCT")
                or line.startswith("DESCRIBE")
            ):
                in_query = True
                current_query.append(line)
            # Query continuation
            elif in_query:
                current_query.append(line)

    # Add last query if exists
    if current_query:
        full_query = "\n".join(prefixes + [""] + current_query)
        queries.append({"comment": "\n".join(current_comment), "query": full_query})

    return queries


def run_query(graph, query_dict, query_num):
    """Execute a SPARQL query and display results"""
    comment = query_dict["comment"]
    query = query_dict["query"]

    print(f"\n{'=' * 70}")
    print(f"QUERY {query_num}")
    print(f"{'=' * 70}")
    print(comment)
    print()

    try:
        start = time.time()
        results = graph.query(query)
        elapsed = time.time() - start

        # Convert results to list to get count
        result_list = list(results)

        print(f"✓ Query executed in {elapsed:.3f} seconds")
        print(f"✓ Results: {len(result_list)} row(s)")
        print()

        # Display results
        if len(result_list) > 0:
            # Get variable names from first result
            if hasattr(results, "vars") and results.vars:
                headers = [str(var) for var in results.vars]

                # Print header
                print("  " + " | ".join(headers))
                print(
                    "  " + "-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1))
                )

                # Print rows (limit to 20 for readability)
                for i, row in enumerate(result_list[:20]):
                    values = []
                    for var in results.vars:
                        val = row[var]
                        # Truncate long URIs
                        val_str = str(val) if val else ""
                        if len(val_str) > 50:
                            val_str = val_str[:47] + "..."
                        values.append(val_str)
                    print("  " + " | ".join(values))

                if len(result_list) > 20:
                    print(f"  ... ({len(result_list) - 20} more rows)")
            else:
                # For boolean results (ASK queries)
                print(f"  Result: {result_list[0] if result_list else 'N/A'}")
        else:
            print("  No results returned.")

    except Exception as e:
        print(f"✗ Query failed: {str(e)}")
        print(f"  Query: {query[:200]}...")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("SPARQL QUERY RUNNER - Madrid Bus Network RDF")
    print("=" * 70)

    # Setup paths
    base_dir = Path(__file__).parent
    rdf_file = base_dir / "madrid-bus-data.nt"
    sparql_file = base_dir / "queries.sparql"

    # Check if files exist
    if not rdf_file.exists():
        print(f"\n✗ ERROR: RDF file not found: {rdf_file}")
        print("  Please run Morph-KGC first to generate the RDF data.")
        return

    if not sparql_file.exists():
        print(f"\n✗ ERROR: SPARQL file not found: {sparql_file}")
        return

    # Load RDF data
    graph = load_rdf_data(rdf_file)

    # Parse SPARQL queries
    print(f"\nParsing queries from: {sparql_file.name}")
    queries = parse_sparql_file(sparql_file)
    print(f"✓ Found {len(queries)} queries")

    # Run each query
    for i, query_dict in enumerate(queries, 1):
        run_query(graph, query_dict, i)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"✓ COMPLETED: Executed {len(queries)} queries")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
