#2 Query, get arrival times of a specific stop
def query_arrival_times(stop_id, time_str):
    query_template = f"""
    PREFIX ont: <http://crtm-urban-buses.org/opendata/handsOn/group11/ontology#>
    PREFIX schema: <http://schema.org/>
    SELECT ?lineName ?destination ?arrivalTime ?departureTime
    WHERE {{
        ?stop a ont:Stop ;
              ont:stopId "{stop_id}" .
        ?stopTime a ont:StopTime ;
                  ont:refersToStop ?stop ;
                  ont:arrivalTime ?arrivalTime ;
                  ont:departureTime ?departureTime ;
                  ont:belongsToTrip ?trip .
        ?trip a ont:Trip ;
              ont:tripHeadsign ?destination ;
              ont:belongsToRoute ?route .
        ?route a ont:BusRoute ;
               ont:routeShortName ?lineName .
        FILTER(?arrivalTime > "{time_str}")
    }}
    ORDER BY ?arrivalTime
    LIMIT 10
    """
    sparql = SPARQLWrapper(GRAPHDB_URL)
    sparql.setQuery(query_template)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return pd.DataFrame([
            {
                "Line": r["lineName"]["value"],
                "Destination": r["destination"]["value"],
                "Arrival": r["arrivalTime"]["value"],
                "Departure": r["departureTime"]["value"]
            } for r in results["results"]["bindings"]
        ])
    except Exception as e:
        st.error(f"Error querying GraphDB: {e}")
        return pd.DataFrame()

