#OD matrix

import pandas as pd
import random

#Import data from excel 
#Note: When separating to culums in Excel go to advanced and set the . and , properly!
df=pd.read_excel('201909-bluebikes-tripdata.xlsx', index_col=None)

#Dropping the colums that are not needed
df = df.drop(['stoptime','start station name','end station name','bikeid', 'usertype','gender','birth year'],1)
df = df.drop(['tripduration','start station id','end station id'],1)

#Select second week of September 2019
df['starttime'] = pd.to_datetime(df['starttime'])
start_date= '2019-09-08 00:00:00'
end_date='2019-09-15 00:00:00'
df=df[(df['starttime'] > start_date) & (df['starttime'] <= end_date)]

#Set indexes for the data of that week
df.reset_index(drop=True, inplace=True)

#Scatter origins and destinations around stations
# The values correspond to 250m in the lat and lon of Boston and follow a normal distribution
for i in range(len(df.index)):
    a_lat= df.at[i,'start station latitude']
    a_new_lat= a_lat + 0.002248*random.gauss(0,1)
    df.at[i,'start station latitude']= a_new_lat

    a_lon= df.at[i,'start station longitude']
    a_new_lon= a_lon + 0.003043*random.gauss(0,1)
    df.at[i,'start station longitude']= a_new_lon

    b_lat= df.at[i,'end station latitude']
    b_new_lat= b_lat + 0.002248*random.gauss(0,1)
    df.at[i,'end station latitude']= b_new_lat

    b_lon= df.at[i,'end station longitude']
    b_new_lon= b_lon + 0.003043*random.gauss(0,1)
    df.at[i,'end station longitude']= b_new_lon
   
#Show in terminal
print(df)

#Save to Excel file
df.to_excel("output.xlsx") 