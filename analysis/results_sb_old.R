library(magrittr)


path_experiments <- "../results/station-based-23-03-2021/"
path_dir <- list.files(path_experiments, full.names = T)

path <- path_dir[175]

config <- jsonlite::fromJSON(file.path(path, "config.json"))
user_trips <- data.table::fread(file.path(path, "user_trips.csv"), na.strings = "None")
bike_trips <- data.table::fread(file.path(path, "bike_trips.csv"), na.strings = "None")


df_config <- data.frame(
  mode = config$MODE, # []
  num_bikes = config$NUM_BIKES, # []
  walk_radius = config$WALK_RADIUS, # [m]
  riding_speed = config$RIDING_SPEED, # [km/h]
  walking_speed = config$WALKING_SPEED, # [km/h]
  magic_beta = config$MAGIC_BETA, # [%]
  magic_min_bikes = config$MAGIC_MIN_BIKES, # []
  magic_min_docks = config$MAGIC_MIN_DOCKS # []
)




# TODO: move all this to dataframe
# num_bikes <- config$NUM_BIKES
# bikes <- seq(1, num_bikes)-1
# num_bikes_used <- user_trips$bike_id %>% na.omit() %>% unique() %>% length()
# num_trips <- user_trips$time_walk_destination %>% na.omit() %>% length()
# time_total <- diff(range(user_trips$time_departure, na.rm=T)) # [s]
# num_days <- time_total / (60*60*24)
# num_trips_bike_day <- num_trips / num_bikes / num_days
# 
# time_in_use <- sum(user_trips$time_ride, na.rm=T)/num_bikes # [s/bike]
# stop_time <- time_total - time_in_use
# stop_time.time <- stop_time / time_total * 100
# 
# time_in_use.bike <- user_trips %>% 
#   dplyr::group_by(bike_id) %>% 
#   dplyr::summarise(time_in_use = sum(time_ride, na.rm=T)) # [s]
# # hist(time_in_use.bike$time_in_use/60, breaks = 50)
# 
# vkt_in_use <- time_in_use * config$RIDING_SPEED / 3.6 / 1000 # [km]
# vkt_in_use.dist <- vkt_in_use / vkt_in_use * 100
# vkt_in_use.time <- time_in_use / time_total * 100



# SEPARATE TRIP PER HOUR (COMPLEX) ------------------------------------

freq <- 30*60
# vkt_in_use per hour
user_trips %>% 
  dplyr::mutate(
    time_ride_start = time_departure + time_walk_origin,
    time_ride_end = time_departure + time_walk_origin + time_ride,
    time_ride_start_hour = floor(time_ride_start / freq),
    time_ride_end_hour = floor(time_ride_end / freq)) %>% 
  dplyr::mutate(
    # separate ride into two consecutive hours (if applies)
    time_ride_first = ifelse(time_ride_start_hour == time_ride_end_hour, 
                             time_ride_end - time_ride_start, 
                             time_ride_end_hour*freq - time_ride_start),
    time_ride_second = ifelse(time_ride_start_hour == time_ride_end_hour,
                              NA, time_ride_end - time_ride_end_hour*freq),
    # this is to remove those hours after pivoting
    time_ride_end_hour = ifelse(time_ride_start_hour==time_ride_end_hour, NA, time_ride_end_hour)
  ) %>% 
  tidyr::pivot_longer(cols=c(time_ride_start_hour, time_ride_end_hour), values_to = "hour") %>% 
  dplyr::group_by(hour) %>% 
  dplyr::mutate(vkt_in_use.hour = sum(time_ride_first, na.rm=T) + sum(time_ride_second, na.rm=T)) %>% 
  dplyr::ungroup() %>% 
  tidyr::pivot_wider() %>% 
  dplyr::filter(!is.na(hour)) %>% 
  dplyr::group_by(hour) %>% 
  dplyr::summarise(
    num_bikes_in_use = dplyr::n(),
    num_bikes_stopped = setdiff(bikes, bike_id) %>% length(),
    stop_time.hour = freq*num_bikes - vkt_in_use.hour,
    vkt_in_use.hour = vkt_in_use.hour * config$RIDING_SPEED / 3.6 / 1000 # [km]
  ) %>% head



# SIMPLE INTERVALS --------------------------------------------------------

user_trips %>% 
  # CONFIG
  merge(df_config) %>% 
  dplyr::summarise(
    # VEHICLES
    time_in_use = sum(time_ride, na.rm=T), # [s]
    time_in_use.bike = time_in_use / num_bikes, # [s/bike]
    
    time_total = diff(range(time_departure, na.rm=T))*num_bikes, # [s]
    time_total.bike = time_total / num_bikes, # [s/bike]
    
    time_stop = time_total - time_in_use, # [s]
    time_stop.bike = time_stop / num_bikes, # [s/bike]
    time_stop.time = time_stop / time_total * 100, # [%]
    
    vkt_in_use = time_in_use * config$RIDING_SPEED / 3.6 / 1000, # [km]
    vkt_in_use.bike = vkt_in_use / num_bikes, # [km/bike]
    vkt_in_use.dist = vkt_in_use / vkt_in_use * 100, # [%]
    vkt_in_use.time = time_in_use / time_total * 100, # [%]
    
    
    
    # USERS
    num_users = dplyr::n(), # []
    time_trip_avg = mean(time_walk_origin + time_ride + time_walk_destination, na.rm=T), # [s]
    time_ride_avg = mean(time_ride, na.rm=T), # [s]
    time_walk_origin_avg = mean(time_walk_origin, na.rm=T), # [s]
    time_walk_destination_avg = mean(time_walk_destination, na.rm=T), # [s]
    
    walk_over_10min = sum(time_walk_origin > 10*60 | time_walk_destination > 10*60, na.rm=T), # []
    walk_over_15min = sum(time_walk_origin > 15*60 | time_walk_destination > 15*60, na.rm=T), # []
    walk_over_10min.user = walk_over_10min/num_users * 100, # [%]
    walk_over_15min.user = walk_over_15min/num_users * 100, # [%]
    
    
    # TRIPS
    num_trips = dplyr::n(), # []
    served_trips = sum(!is.na(time_walk_destination)), # []
    unserved_trips = num_trips - served_trips, # []
    unserved_trips_no_stations = sum(is.na(time_walk_origin)), # []
    unserved_trips_no_bikes = sum(is.na(time_walk_origin)), # NO INFORMATION FOR THIS
    
    num_origin_visited_stations = origin_visited_stations %>% stringr::str_split(";") %>% unlist() %>% 
      as.numeric() %>% na.omit() %>% sapply(length) %>% sum,
    num_destination_visited_stations = destination_visited_stations %>% stringr::str_split(";") %>% unlist() %>% 
      as.numeric() %>% na.omit() %>% sapply(length) %>% sum,
    good_experience_trips = served_trips - num_origin_visited_stations,
    bad_experience_trips = served_trips - num_origin_visited_stations,
    
    num_days = time_total.bike / (60 * 60 * 24), # [day]
    num_trips_bike_day = served_trips / num_bikes / num_days, # []
    
    # TODO
  ) %>% dplyr::distinct() %>% head

freq <- 60*60
bikes_id <- seq(config$NUM_BIKES)-1
user_trips %>% 
  # CONFIG
  merge(df_config) %>% 
  dplyr::mutate(
    time = time_departure,
    interval = floor(time / freq),
    
    # AUXILIAR
    time_trip = time_walk_origin + time_ride + time_walk_destination,
  ) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarise(
    # VEHICLES
    time_in_use.hour = sum(time_ride, na.rm=T), # [s]
    vkt_in_use.hour =  time_in_use.hour * config$RIDING_SPEED / 3.6 / 1000, # [km], PER BIKE??
    time_stop.hour = freq*num_bikes - time_in_use.hour, #  [s]
    num_bikes_in_use.hour = sum(!is.na(bike_id)), # unique(bike_id) %>% length(), # []
    num_bikes_stopped.hour = setdiff(bikes_id, bike_id) %>% length(), # []
    
    # USERS
    num_users.hour = dplyr::n(), # []
    time_trip_avg.hour = mean(time_trip, na.rm=T), # [s]
    time_ride_avg.hour = mean(time_ride, na.rm=T), # [s]
    time_walk_origin_avg.hour = mean(time_walk_origin, na.rm=T), # [s]
    time_walk_destination_avg.hour = mean(time_walk_destination, na.rm=T), # [s]
    
    
  ) %>% 
  dplyr::ungroup() %>% dplyr::distinct() %>% head() %>% View
  

