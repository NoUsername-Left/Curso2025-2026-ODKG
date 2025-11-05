# Hands-on 3 – Self-Assessment

## Data–Ontology Consistency Checklist

### Resources (CSV)
- [✔] Every resource has a unique identifier in a column (not auto-incremented).
- [✔] Every resource is related to a class in the ontology.

### Classes (Ontology)
- [✔] Every class is related to at least one resource described in the CSV file.

### Columns (CSV)
- [✔] All values are trimmed (no leading/trailing whitespace).
- [✔] All values are properly encoded (e.g., dates, booleans).
- [✔] Every column is related to a property in the ontology.

### Properties (Ontology)
- [✔] Every property is related to a column in the CSV file.

---

## 1. Dataset Description

- **Source: https://ropenspain.github.io/spanishoddata/articles/v2-2022-onwards-mitma-data-codebook This source explains the origin of the data, it's purpose and the meaning of every variable of the flux_daily_move.csv dataset**
- **Format: CSV (`.csv`)**
- **Number of rows: 748 595**
- **Number of columns: 11**
- **Short description: This dataset describes the trips between Madrid and other cities. It contains data such as the number of travellers per trip, the total number of kilometers for this trip and some of their characteristics : income, age, gender, …
For example, line 1 describes the Following : there are 6189 trips from Madrid (id_origin 28079) to Vitoria Gasteiz (id_destination 01059)of males people aged 0 to 25, with an income between 10 to 15 thousand. And the total distance travelled (by adding every person doing this trip) is 1765301 km**

## 2. Data Quality Issues Identified

Overall the data was very clean.
The numbers values were in text type, and the decimals were ambiguous. We fixed it by checking verified data online (for example the distance in kilometers between cities).
But no missing value, no dupplicate and no incorrect data.

---

## 3. Cleaning & Transformation Steps

Cf Json document.

---

Dataset 2

## 1. Dataset Description

- **Source: https://ropenspain.github.io/spanishoddata/articles/v2-2022-onwards-mitma-data-codebook This source explains the origin of the data, it's purpose and the meaning of every variable of the zones.csv dataset**
- **Format: CSV (`.csv`)**
- **Number of rows: 2618 **
- **Number of columns:3**
- **Short description: This dataset represents spanish cities that have relations with Madrid by any transport. Each line represents one city with 3 columns : identifier, city name, and population. The values in the column identifier are in common with the "flux_daily_move.csv" dataset which represents the characteristics of trips (lenght, number of travellers, age, gender of travellers, etc). Therefore, this allows us to link both dataset. **

## 2. Data Quality Issues Identified
The population column was filled with text values instead of numbers. Therefore, we converted the values to numbers.

---

## 3. Cleaning & Transformation Steps

Cf Json document.
