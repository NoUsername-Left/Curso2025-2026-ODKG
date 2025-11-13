from rdflib import Graph, Namespace
from functools import lru_cache
from urllib.parse import unquote

SC = Namespace("http://smartcity.linkeddata.es/lcc/ontology#")
SCHEMA = Namespace("https://schema.org/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
DBO = Namespace("http://dbpedia.org/ontology/")

ONTO_FILE = "../ontology/ontology.ttl"
DATA_FILE = "../data/tripletas-Final.nt"
    

@lru_cache(maxsize=1)
def get_graph() -> Graph:
    g = Graph()
    g.parse(ONTO_FILE, format="turtle")
    g.parse(DATA_FILE, format="nt")
    return g

# Mapa “bonito” -> nombre mostrado en UI -> nombre local de clase en tu ontología
FACILITY_CLASS_MAP = {
    # Clases Principales
    "Library": "sc:Library",
    "Park/Garden": "sc:Park",
    "Sports Center": "sc:SportsCenter",
    "Educational Institution": "sc:EducationalInstitution",
    # Mas subclases
    #"Residence hall": "sc:ResidenceHall",
    #"Faculty": "sc:Faculty",
    #"University school": "sc:UniversitySchool",
    #"Other centers": "sc:OtherCenters",

    #"Gym": "sc:Gym",
    #"FootballField": "sc:FootballField",
    #"SwimmingPool": "sc:SwimmingPool",
    #"Tennis court": "sc:TennisCourt",
    #"Climbing wall": "sc:ClimbingWall",
    #"Rowing pier": "sc:RowingPier",
    #"Stadium": "sc:Stadium",
    #"Basketball court": "sc:BasketballCourt"
}

def _norm_coord(val: object, kind: str) -> float | None:
    """
    Normaliza coordenadas provenientes de literales raros (p.ej. '4.045.750.817.868.430').
    kind: 'lat' | 'lon'
    """
    if val is None:
        return None
    s = str(val).strip()
    # Unificar separadores
    s = s.replace(" ", "").replace(",", ".")
    # Si hay más de un punto -> vienen "agrupados": quita todos y re-coloca el decimal
    if s.count(".") > 1:
        s = s.replace(".", "")  # quita todos
        # inserta '.' tras los grados (2 dígitos para lat 40.., 1 dígito para lon -3..)
        if kind == "lat":
            # ej: '4045750817868430' -> '40.45750817868430'
            if len(s) >= 3:
                s = s[:2] + "." + s[2:]
        else:  # lon (Madrid ~ -3.xxx)
            # conserva signo si lo hay
            sign = ""
            if s.startswith("-"):
                sign, s = "-", s[1:]
            if len(s) >= 2:
                s = sign + s[:1] + "." + s[1:]
            else:
                s = sign + s  # no tocar si es rarísimo
    try:
        f = float(s)
        # sanity-check
        if kind == "lat" and not (-90 <= f <= 90):
            return None
        if kind == "lon" and not (-180 <= f <= 180):
            return None
        return f
    except Exception:
        return None

def _pretty_class(uri_or_label: str | None) -> str | None:
    """Devuelve un nombre de clase legible (sin prefijos ni URIs)."""
    if not uri_or_label:
        return None
    s = str(uri_or_label)
    # Quita prefijos schema:, sc:, o URIs completas
    s = s.replace("schema:", "").replace("sc:", "")
    if "/" in s or "#" in s:
        s = s.split("/")[-1].split("#")[-1]
    return s

def get_facilities_by_type(class_label: str):
    """
    Devuelve facilities (con datos básicos y territorio) de una subclase concreta.
    class_label es la clave visible (p.ej. 'Library'); se traduce a schema:Library o sc:SportsCenter
    """
    g = get_graph()
    local = FACILITY_CLASS_MAP[class_label]

    # Determinar si estamos usando 'schema' o 'sc' para la consulta
    prefix = local.split(":")[0]  # 'schema' o 'sc'

    # Aquí modificamos el prefijo en función de la clase
    q = f"""
    PREFIX schema: <{SCHEMA}>
    PREFIX sc: <{SC}>
    PREFIX geo: <{GEO}>
    PREFIX dbo: <{DBO}>

    SELECT DISTINCT ?facility ?name ?lat ?long ?tel ?email
                    ?nhName ?distName ?munName
    WHERE {{
      ?facility a ?class ;
                schema:name ?name .

      FILTER(
        ?class = {local} ||
        STR(?class) = REPLACE(STR({local}), "ontology#", "resource/")
      )

      OPTIONAL {{ ?facility geo:lat ?lat . }}
      OPTIONAL {{ ?facility geo:long ?long . }}
      OPTIONAL {{ ?facility schema:telephone ?tel . }}
      OPTIONAL {{ ?facility schema:email ?email . }}

      OPTIONAL {{
        ?facility schema:containedInPlace ?nh .
        OPTIONAL {{ ?nh schema:name ?nhName . }}
      }}
      OPTIONAL {{
        ?facility schema:containedInPlace ?dist .
        OPTIONAL {{ ?dist schema:name ?distName . }}
      }}
      OPTIONAL {{
        ?facility schema:containedInPlace ?mun .
        OPTIONAL {{ ?mun schema:name ?munName . }}
      }}
    }}
    """

    rows = g.query(q)
    results = []
    for r in rows:
        results.append({
            "uri": str(r.facility),
            "name": str(r.name) if r.name else None,
            "lat": _norm_coord(r.lat, "lat"),
            "long": _norm_coord(r.long, "lon"),
            "telephone": str(r.tel) if r.tel else None,
            "email": str(r.email) if r.email else None,
            "neighbourhood": str(r.nhName) if r.nhName else None,
            "district": str(r.distName) if r.distName else None,
            "municipality": str(r.munName) if r.munName else None,
            "class": _pretty_class(local),
        })
    return results


def get_neighbourhoods():
    """Lista de barrios (uri, nombre) detectados a partir de las facilities."""
    g = get_graph()
    q = f"""
    PREFIX schema: <{SCHEMA}>
    SELECT DISTINCT ?nh (REPLACE(STR(?nh), "^.*neighbourhood/", "") AS ?rawName)
    WHERE {{
      ?facility schema:containedInPlace ?nh .
      FILTER(CONTAINS(LCASE(STR(?nh)), "neighbourhood"))
    }}
    ORDER BY LCASE(STR(?rawName))
    """
    results = []
    for r in g.query(q):
        uri = str(r.nh)
        raw_name = str(r.rawName)
        name = unquote(raw_name)  # decodifica %20, %C3... → espacios y acentos normales
        results.append((uri, name))
    return results

def get_facilities_in_neighbourhood(nh_uri: str):
    """Devuelve todas las facilities de cualquier tipo que están en el barrio indicado."""
    g = get_graph()
    q = f"""
    PREFIX sc: <{SC}>
    PREFIX schema: <{SCHEMA}>
    PREFIX geo: <{GEO}>
    PREFIX dbo: <{DBO}>

    SELECT DISTINCT ?facility ?name ?lat ?long ?tel ?email ?classLocal ?distName ?munName
    WHERE {{
      # La instalación debe pertenecer al barrio seleccionado
      ?facility schema:containedInPlace <{nh_uri}> ;
                schema:name ?name .

      OPTIONAL {{ ?facility geo:lat ?lat . }}
      OPTIONAL {{ ?facility geo:long ?long . }}
      OPTIONAL {{ ?facility schema:telephone ?tel . }}
      OPTIONAL {{ ?facility schema:email ?email . }}

      # Recuperar su clase concreta (Library, Park, SportsCenter, etc.)
      OPTIONAL {{
        ?facility a ?class .
        FILTER(?class != sc:Facility)
        BIND(REPLACE(REPLACE(STR(?class), "^.*/", ""), "^.*#", "") AS ?classLocal)
      }}

      OPTIONAL {{
        ?facility schema:containedInPlace ?dist .
        ?dist a dbo:District .
        OPTIONAL {{ ?dist schema:name ?distName . }}
      }}
      OPTIONAL {{
        ?facility schema:containedInPlace ?mun .
        ?mun a dbo:Municipality .
        OPTIONAL {{ ?mun schema:name ?munName . }}
      }}
    }}
    ORDER BY ?name
    """
    rows = g.query(q)
    out = []
    for r in rows:
        out.append({
            "uri": str(r.facility),
            "name": str(r.name),
            "lat": _norm_coord(r.lat, "lat"),
            "long": _norm_coord(r.long, "lon"),
            "telephone": str(r.tel) if r.tel else None,
            "email": str(r.email) if r.email else None,
            "class": _pretty_class(r.classLocal),
            "district": str(r.distName) if r.distName else None,
            "municipality": str(r.munName) if r.munName else None,
        })
    return out

def get_districts():
    """Lista de distritos (uri, nombre) detectados a partir de las facilities."""
    g = get_graph()
    q = f"""
    PREFIX schema: <{SCHEMA}>
    PREFIX dbo: <{DBO}>
    SELECT DISTINCT ?district (REPLACE(STR(?district), "^.*district/", "") AS ?rawName)
    WHERE {{
      ?facility schema:containedInPlace ?nh .
      ?nh sc:locatedInDistrict ?district .
      FILTER(CONTAINS(LCASE(STR(?district)), "district"))
    }}
    ORDER BY LCASE(STR(?rawName))
    """
    results = []
    for r in g.query(q):
        uri = str(r.district)
        raw_name = str(r.rawName)
        name = unquote(raw_name)  # decodifica %20, %C3... → espacios y acentos normales
        results.append((uri, name))
    return results


def get_neighbourhoods_in_district(district_uri: str):
    """Devuelve todos los barrios dentro de un distrito específico."""
    g = get_graph()
    q = f"""
    PREFIX schema: <{SCHEMA}>
    PREFIX dbo: <{DBO}>
    SELECT DISTINCT ?nh (REPLACE(STR(?nh), "^.*neighbourhood/", "") AS ?rawName)
    WHERE {{
      ?facility schema:containedInPlace ?nh .
      ?nh sc:locatedInDistrict <{district_uri}> .
      FILTER(CONTAINS(LCASE(STR(?nh)), "neighbourhood"))
    }}
    ORDER BY LCASE(STR(?rawName))
    """
    results = []
    for r in g.query(q):
        uri = str(r.nh)
        raw_name = str(r.rawName)
        name = unquote(raw_name)  # decodifica %20, %C3... → espacios y acentos normales
        results.append((uri, name))
    return results


def get_nearby_transport(facility_uri: str):
    """
    Devuelve el transporte cercano (Subway, Bus, Train) para una facility dada.
    """
    g = get_graph()
    q = f"""
    PREFIX sc: <{SC}>
    PREFIX schema: <{SCHEMA}>
    PREFIX dbo: <{DBO}>

    SELECT DISTINCT ?transport ?transportClass
    WHERE {{
      <{facility_uri}> sc:hasNearby ?transport .  # La facility tiene cerca un transporte público
      ?transport a ?transportClass .  # El transporte es de una clase
      FILTER(?transportClass IN (sc:Subway, sc:Bus, sc:Train))  # Filtrar solo por Subway, Bus, y Train
    }}
    """

    rows = g.query(q)
    
    # Estructuramos los resultados por tipo de transporte
    transport = {"Subway": [], "Bus": [], "Train": []}
    
    for r in rows:
        # Extraemos el nombre del transporte a partir del URI después de "resource/"
        transport_name = str(r.transport).split("resource/")[-1]
        # Eliminar los prefijos de transporte como "subway", "suburbantrain" y "bus" al principio del nombre
        if transport_name.startswith("subway"):
            transport_name = transport_name.replace("subway/", "").strip(":")  # Elimina "subway" y el colon al final
        elif transport_name.startswith("suburbantrain"):
            transport_name = transport_name.replace("suburbantrain/", "").strip(":")  # Elimina "suburbantrain"
        elif transport_name.startswith("bus"):
            transport_name = transport_name.replace("bus/", "").strip(":")  # Elimina "bus"
        
        # Decodificamos el nombre del transporte para convertir caracteres codificados (como %20) a su forma normal
        transport_name = unquote(transport_name)
        transport_class = str(r.transportClass).split("#")[-1]  # Obtener el nombre de la clase de transporte
        
        if transport_class in transport:
            transport[transport_class].append(transport_name)
    
    return transport

'''
#FUNCIONES DESCARTADAS
def get_neighbourhoods1():
    """Lista de barrios (uri, nombre) ordenados alfabéticamente."""
    g = get_graph()
    q = f"""
    PREFIX schema: <{SCHEMA}>
    PREFIX dbo: <{DBO}>
    SELECT DISTINCT ?nh (COALESCE(?nLabel, REPLACE(STR(?nh), "^.*neighbourhood/", "")) AS ?name)
    WHERE {{
      ?nh a dbo:Neighbourhood .
      OPTIONAL {{ ?nh schema:name ?nLabel . }}
    }}
    ORDER BY LCASE(STR(?name))
    """
    return [(str(r.nh), str(r.name)) for r in g.query(q)]


def get_facilities_in_neighbourhood1(nh_uri: str):
    """Facilities contenidas en un barrio concreto (por URI del barrio)."""
    g = get_graph()
    q = f"""
    PREFIX sc: <{SC}>
    PREFIX schema: <{SCHEMA}>
    PREFIX geo: <{GEO}>
    PREFIX dbo: <{DBO}>

    SELECT DISTINCT ?facility ?name ?lat ?long ?tel ?email ?classLocal ?distName ?munName
    WHERE {{
      ?facility a sc:Facility ;
                schema:name ?name ;
                schema:containedInPlace ?nh .

      # Compara URIs ignorando mayúsculas/minúsculas
      FILTER(lcase(str(?nh)) = lcase(str(<{nh_uri}>)))

      OPTIONAL {{ ?facility geo:lat ?lat . }}
      OPTIONAL {{ ?facility geo:long ?long . }}
      OPTIONAL {{ ?facility schema:telephone ?tel . }}
      OPTIONAL {{ ?facility schema:email ?email . }}

      OPTIONAL {{
        ?facility a ?class .
        FILTER(?class != sc:Facility)
        BIND(REPLACE(STR(?class), "^.*#", "") AS ?classLocal)
      }}
    }}
    """

    rows = g.query(q)
    out = []
    for r in rows:
        out.append({
            "uri": str(r.facility),
            "name": str(r.name),
            "lat": _norm_coord(r.lat, "lat"),
            "long": _norm_coord(r.long, "lon"),
            "telephone": str(r.tel) if r.tel else None,
            "email": str(r.email) if r.email else None,
            "class": _pretty_class(r.classLocal),
            "district": str(r.distName) if r.distName else None,
            "municipality": str(r.munName) if r.munName else None,
        })
    return out

def get_nearby_transport(facility_uri: str):
    """Transporte cercano (nombre + clase) para una facility."""
    g = get_graph()
    q = f"""
    PREFIX sc: <{SC}>
    PREFIX schema: <{SCHEMA}>
    SELECT DISTINCT ?t ?tName ?tClassLocal
    WHERE {{
      <{facility_uri}> sc:hasNearby ?t .
      ?t a ?tClass .
      FILTER(?tClass IN (sc:Subway, sc:Bus, sc:SuburbanTrain))
      OPTIONAL {{ ?t schema:name ?tName . }}
      BIND(REPLACE(STR(?tClass), "^.*#", "") AS ?tClassLocal)
    }}
    ORDER BY ?tClassLocal ?tName
    """
    rows = g.query(q)
    by_class = {"Subway": [], "Bus": [], "SuburbanTrain": []}
    for r in rows:
        c = str(r.tClassLocal)
        label = str(r.tName) if r.tName else r.t
        if c in by_class:
            by_class[c].append(label)
    return by_class

'''