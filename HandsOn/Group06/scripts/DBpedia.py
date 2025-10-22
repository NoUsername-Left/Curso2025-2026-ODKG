import pandas as pd
import time
from SPARQLWrapper import SPARQLWrapper, JSON
import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()

# Input/output CSV paths
input_csv = "HandsOn/Group06/csv/df_final-updated.csv"
output_csv = "HandsOn/Group06/csv/df_with_wikidata_links.csv"

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
import socket

def get_wikidata_link(lat, lon, retries=2):
    query = f"""
    SELECT ?item ?distance WHERE {{
      SERVICE wikibase:around {{
        ?item wdt:P625 ?coord .
        bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral .
        bd:serviceParam wikibase:radius "10" .
        bd:serviceParam wikibase:distance ?distance .
      }}
    }}
    ORDER BY ?distance
    LIMIT 1
    """
    sparql.setQuery(query)
    for attempt in range(retries + 1):
        try:
            # Set a custom timeout for the HTTP request (default is no timeout)
            sparql.setTimeout(15)
            results = sparql.query().convert()
            bindings = results['results']['bindings']
            if bindings:
                return bindings[0]['item']['value']
            else:
                return None
        except (SPARQLExceptions.EndPointNotFound, socket.timeout) as e:
            print(f"Timeout or endpoint not found for ({lat}, {lon}), attempt {attempt + 1}")
            if attempt == retries:
                return None
        except Exception as e:
            print(f"Error for ({lat}, {lon}), attempt {attempt + 1}: {e}")
            if attempt == retries:
                return None
    return None
    

df = pd.read_csv(input_csv)
# Make sure coordinates are floats and drop rows without them
df = df.dropna(subset=['stop_lat', 'stop_lon'])
df['stop_lat'] = df['stop_lat'].astype(float)
df['stop_lon'] = df['stop_lon'].astype(float)

# Build the link column efficiently with progress printout
links = []
for idx, row in df.iterrows():
    lat, lon = row['stop_lat'], row['stop_lon']
    wikidata_link = get_wikidata_link(lat, lon)
    links.append(wikidata_link)
    print(f"{idx}: {wikidata_link}")
    time.sleep(0.5)  # Respect Wikidata's usage policy

df['wikidata_link'] = links
df.to_csv(output_csv, index=False)
print(f"Done! Results written to {output_csv}")

