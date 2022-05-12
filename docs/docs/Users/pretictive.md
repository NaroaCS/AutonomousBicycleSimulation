---
sidebar_position: 4
label: Demand prediction
---
# Demand prediction

While we provide the results for our demand prediction in the file *demad_grid.csv*, we detail here the procedure that was followed to generate such files:

1. Download the historical trip data from **[Bluebikes](https://www.bluebikes.com/system-data)** and save it in a folder ‘bluebikes_data’ within the Preprocessing folder

2. Rscript training_data.R (input bluebikes_data → outputs training_data.csv)

3. python3 gccn_ddgf.py (input training_data.csv → outputs testing_data.csv)

4. Rscript testing_data.R (input testing_data.csv → outputs demand_grid.csv)
