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

#3 Given a line bus and direction, get route
def get_stops_by_direction(line_id, direction="0"):
    query_template = f"""
    PREFIX ont: <http://crtm-urban-buses.org/opendata/handsOn/group11/ontology#>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
    PREFIX schema: <http://schema.org/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT DISTINCT ?stopId ?stopName ?seq ?lat ?lon
    WHERE {{
        ?route a ont:BusRoute ;
               ont:routeShortName "{line_id}" .
        ?trip a ont:Trip ;
              ont:belongsToRoute ?route ;
              ont:directionId "{direction}" .
        ?stopTime a ont:StopTime ;
                  ont:belongsToTrip ?trip ;
                  ont:stopSequence ?seq ;
                  ont:refersToStop ?stop .
        ?stop a ont:Stop ;
              ont:stopId ?stopId ;
              schema:name ?stopName ;
              geo:lat ?lat ;
              geo:long ?lon .
    }}
    ORDER BY ASC(xsd:integer(?seq))
    LIMIT 100
    """
    sparql = SPARQLWrapper(GRAPHDB_URL)
    sparql.setQuery(query_template)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return [
            {
                "Sequence": int(r["seq"]["value"]),
                "Stop_ID": r["stopId"]["value"],
                "Stop_Name": r["stopName"]["value"],
                "Latitude": float(r["lat"]["value"]),
                "Longitude": float(r["lon"]["value"]),
                "Direction": direction
            }
            for r in results["results"]["bindings"]
        ]
    except Exception as e:
        st.error(f"Error querying GraphDB: {e}")
        return []