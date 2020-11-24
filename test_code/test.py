#bike information for SB -> id and initial station id
bikes_data = [] 
mode=0
n_bikes=15

if mode==1 or mode==2:
    i=0
    while i<n_bikes:
        bike=[i,0,0]
        bikes_data.append(bike) 
        i+=1
elif mode==0:
    i=0
    while i<n_bikes:
        station_id=24 # Set random station 
        bike=[i,station_id,0,1]    
        bikes_data.append(bike)
        i+=1

print(bikes_data)
for bike_id, bike_data in enumerate(bikes_data): 
    #mode = bike_data['mode'] #Takes the mode 
    if mode == 0:
        print(bike_id, bike_data[2]) 
        #station_id = bike_data[1]

