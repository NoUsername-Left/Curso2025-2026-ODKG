## Group Members

- **Emanuele Emilio Alberti**  
  GitHub: [emaalberti](https://github.com/emaalberti)

- **Leandro Duarte**  
  GitHub: [Leandr0Duar7e](https://github.com/Leandr0Duar7e)

- **Kada Ivana Haala**  
  GitHub: [bombaHKI](https://github.com/bombaHKI)

- **Ottavia Biagi**  
  GitHub: [OttaviaBiagi](https://github.com/OttaviaBiagi)

---

## Generate Full Dataset Locally

**Note:** This repository contains only sample data (500 rows). The full RDF datasets are ~5GB each and cannot be versioned in Git. To reproduce the complete datasets:

### 1. Download Raw Data
Download GTFS data from [Mobility Database](https://mobilitydatabase.org/feeds/gtfs/mdb-2820) and extract the `.txt` files into:
```
Group06/data/raw/
```

Create the output directory:
```bash
mkdir -p data/processed
```

### 2. Setup Python Environment
```bash
cd scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Process Data
```bash
python preprocessing.py        # Converts GTFS files to CSV
python assignment3.py         # Cleans data, fixes dates
python linking.py            # Creates local areas with Wikidata links
```

**Note:** The `linking.py` script can take ~1 hour to complete as it queries Wikidata for all 7,852 bus stops to gather geographic area information and owl:sameAs links.

### 4. Generate RDF Data
**Base dataset (no external links):**
```bash
cd ../morph-kgc
# Use default configuration.ini (points to madrid-bus-rml.rml)
python3 -m morph_kgc configuration.ini
```
Output: `rdf/madrid-bus-data.nt` (~5GB)

**With Wikidata links:**
Edit `morph-kgc/configuration.ini`:
- Set `mappings=../mappings/madrid-bus-rml-with-links.rml`
- Set `output_file=../rdf/madrid-bus-data-with-links.nt`
```bash
python3 -m morph_kgc configuration.ini
```
Output: `rdf/madrid-bus-data-with-links.nt` (~5GB)

### 5. Validate with SPARQL Queries
```bash
# Base dataset validation
python scripts/query_runner.py

# Wikidata links validation
python scripts/query_runner.py --links
```

Both commands:
- Load RDF file using LightRDF streaming (handles 5GB+ files)
- Compare CSV vs RDF statistics
- Execute relevant SPARQL queries
- Validate owl:sameAs links for Wikidata integration