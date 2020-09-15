#Visualize OD

import pandas as pd
import matplotlib.pyplot as plt
import random

#Read excel file
df=pd.read_excel('output.xlsx')

#Visualize the data taking lat, lon as x,y   
plt.scatter(x=df['start station longitude'], y=df['start station latitude'], s=2,color='coral',alpha=0.5)
plt.scatter(x=df['end station longitude'], y=df['end station latitude'],s=2,color='purple',alpha=0.5)
plt.show()


