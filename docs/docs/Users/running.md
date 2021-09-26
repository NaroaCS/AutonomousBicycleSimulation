---
sidebar_position: 2
label: Running the model
---

# Running the model

## Single run

To run a single simulation, we first need to import the necessary python packages.

### 1. Import libraries

```python
import json
import pandas as pd
from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration
```

* *json* : to read the configuration json file
* *pandas* : to read the stations and users csv
* *SimulationEngine* : to call and execute the simulation
* *BikeGeneration*: to generate the bikes initial location and metadata

### 2. Import data and generate bikes

The second step is to indicate the path of the configuration, stations, and users files, and import them into memory.
The **BikeGeneration** function is used to generate bikes and their initial location. Using this function, bikes are generated randomly at stations, with a probability proportional to their capacity. 

The parameters of the **BikeGeneration** function are: * **fleet size** (indicated at the *NUM_BIKES* parameter), the **system mode** (0: station-based, 1: dockless, 2: autonomous, indicated at the *MODE* parameter) and the **station file path**. The returned object is a *pandas.DataFrame* with the stations information and the number of bikes assigned to each station.

```python
config_path = "data/config.json"
stations_path = "data/stations.csv"
users_path = "data/users.csv"

with open(config_path) as f:
    config = json.load(f)

stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
users_data = pd.read_csv(users_path)
```

### 3. Run simulation

The last step is to simply create the *SimulationEngine* class and the execute the **run** function, indicating maximum simulated time (in seconds) to be executed.
In this example, one hour (3600 seconds) of simulated time would be executed.

```python
city = SimulationEngine(config, stations_data, users_data)
city.run(until=3600)
```

### Complete example

Here is the complete code example:

```python
import json
import pandas as pd
from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration

config_path = "config.json"
stations_path = "stations.csv"
users_path = "users.csv"

with open(config_path) as f:
    config = json.load(f)

stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
users_data = pd.read_csv(users_path)

city = SimulationEngine(config, stations_data, users_data)
city.run(until=3600)
```

## Batch experiments

To run a batch of simulations with different configuration files, we can use the single-run example as a template and repeat the call to the simulation for each desired configuration. For example, given two configuration files *configA.json* and *configB.json*, a simple **for** loop can help to sequentially execute a simulation for each configuration file. 


```python
import json
import pandas as pd
from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration

configuration_paths = ["configA.json", "configB.json"]
stations_path = "stations.csv"
users_path = "users.csv"

for config_path in configuration_paths:

    with open(config_path) as f:
        config = json.load(f)

    stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
    users_data = pd.read_csv(users_path)

    city = SimulationEngine(config, stations_data, users_data)
    city.run(until=3600)
```