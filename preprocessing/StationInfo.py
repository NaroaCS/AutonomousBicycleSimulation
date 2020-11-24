
import pandas as pd

stations=pd.read_excel('current_bluebikes_stations.xlsx', index_col='Number')

stations = stations.drop(['Name','District','Public'],1)

stations.to_excel("bluebikes_stations.xlsx") 