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

This repository contains only sample data. To generate the full dataset:

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
python preprocessing.py
python assignment3.py
python gen_area.py
```

### 4. Generate RDF Data
```bash
cd ../morph-kgc
python3 -m morph_kgc configuration.ini
```

The full RDF data will be generated at `rdf/madrid-bus-data.nt`.