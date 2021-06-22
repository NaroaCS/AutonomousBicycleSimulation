library(magrittr)

path <- "../results/2021-05-02_23-37-15/"

config <- jsonlite::fromJSON(file.path(path, "config.json"))
user_trips <- data.table::fread(file.path(path, "user_trips.csv"), na.strings = "None")
bike_trips <- data.table::fread(file.path(path, "bike_trips.csv"), na.strings = "None")

# DATES -------------------------------------------------------------------

origin <- "2019-10-07"
freq_hour <- 60*60
freq_day <- 24*60*60
peak_times <- c(seq(7*60+50, 9*60+30), seq(15*60+50, 18*60+30))

freq <- 15*60
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarise(
    demand = dplyr::n(),
    served = sum(!is.na(time_ride)),
    unserved = sum(is.na(time_ride)),
  ) %>% 
  dplyr::ungroup() %>% 
  tidyr::pivot_longer(cols=c(demand, served, unserved)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")


freq <- 15*60
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarise(
    used_bikes = length(unique(bike_id)),
    served = sum(!is.na(time_ride)),
    num_bikes = config$NUM_BIKES,
  ) %>% 
  dplyr::ungroup() %>% 
  tidyr::pivot_longer(cols=c(used_bikes, served, num_bikes)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")


bike_trips %>% 
  dplyr::filter(trip_type == 3) %>% View

