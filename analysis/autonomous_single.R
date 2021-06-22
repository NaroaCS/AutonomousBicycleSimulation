library(magrittr)

# path_experiments <- "../results/station-based-23-03-2021/"
# path_dir <- list.files(path_experiments, full.names = T)

path <- "../results/2021-04-20_23-35-47/"

config <- jsonlite::fromJSON(file.path(path, "config.json"))
user_trips <- data.table::fread(file.path(path, "user_trips.csv"), na.strings = "None")
bike_trips <- data.table::fread(file.path(path, "bike_trips.csv"), na.strings = "None")


pdf("output_autonomous.pdf", width = 12, height=8)


df_config <- data.frame(
  mode = config$MODE, # []
  num_bikes = config$NUM_BIKES, # []
  autonomous_radius = config$AUTONOMOUS_RADIUS, # [m]
  riding_speed = config$RIDING_SPEED, # [km/h]
  autonomous_speed = config$AUTONOMOUS_SPEED, # [km/h]
  battery_min_level = config$BATTERY_MIN_LEVEL, # [%]
  battery_autonomy = config$BATTERY_AUTONOMY, # [km]
  battery_charge_time = config$BATTERY_CHARGE_TIME # [h]
)


# DATES -------------------------------------------------------------------

origin <- "2019-10-07"
freq_hour <- 60*60
freq_day <- 24*60*60
peak_times <- c(seq(7*60+50, 9*60+30), seq(15*60+50, 18*60+30))
date_breaks <- seq(lubridate::ymd_hm('2019-10-07 12:00'),lubridate::ymd_hm('2019-10-14 12:00'),by='day')
date_minor_breaks <- seq(lubridate::ymd_hm('2019-10-07 00:00'),lubridate::ymd_hm('2019-10-15 00:00'),by='12 hours')



# USER EVENTS -------------------------------------------------------------

events <- c("wait", "ride")
user_trips %>% 
  dplyr::filter(!is.na(time_ride)) %>% 
  dplyr::mutate(
    time_wait_start = time_departure,
    time_wait_stop = time_departure + time_wait,
    time_ride_start = time_departure + time_wait,
    time_ride_stop = time_departure + time_wait + time_ride
  ) %>% 
  tidyr::pivot_longer(cols=c(time_wait_start, time_wait_stop,
                             time_ride_start, time_ride_stop), 
                      names_to = "event", values_to="ts") %>% 
  dplyr::mutate(event_class = stringr::str_match(event, paste0(events, collapse="|"))) %>% 
  dplyr::arrange(ts) %>%
  dplyr::group_by(event_class) %>% 
  dplyr::mutate(
    increment = stringr::str_ends(event, "start"),
    increment = ifelse(increment, 1, -1),
    count = cumsum(increment)) %>% 
  dplyr::ungroup()%>% 
  dplyr::arrange(ts) %>%
  dplyr::mutate(
    # delta = ts - dplyr::lag(ts),
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times,
    peak = peak != dplyr::lag(peak)
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_vline(data = . %>% dplyr::filter(peak), 
                     ggplot2::aes(xintercept=date), alpha=0.5)+
  ggplot2::geom_line(ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  # ggplot2::ggtitle("Trips activities: by discrete events")+
  ggplot2::theme_bw()




# TRIPS SERVED / UNSERVED ---------------------------------------------------------------

# per interval
freq <- 15*60
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    num_trips = dplyr::n(),
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(num_trips, served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::ggtitle("Trips served / unserved")+
  ggplot2::theme_bw()


# per interval, in percentage
freq <- 15*60
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    num_trips = dplyr::n(),
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride)),
  ) %>%
  dplyr::ungroup() %>% 
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  # ggplot2::geom_area(ggplot2::aes(x=date, y=value, fill=name))+
  ggplot2::geom_area(ggplot2::aes(x=date, y=value, fill=name), position="fill")+
  # ggplot2::geom_col(ggplot2::aes(x=date, y=value, fill=name, alpha=num_trips), position="fill")+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::ggtitle("Trips served / unserved")+
  ggplot2::theme_bw()



# TIME RIDE/WAIT/TRIP DISTRIBUTION -------------------------------------------------------

# density plot
user_trips %>% 
  dplyr::mutate(
    finished = !is.na(time_ride),
    time_trip = time_wait + time_ride,
  ) %>% 
  # dplyr::filter(finished) %>% 
  tidyr::pivot_longer(cols=c(time_trip, time_wait, time_ride)) %>% 
  ggplot2::ggplot()+
  # ggplot2::geom_density(ggplot2::aes(x=value/60, fill=name), alpha=0.1)+
  ggridges::geom_density_ridges(ggplot2::aes(x=value/60, y=name), na.rm=T,
                                scale = 1.2, alpha = 0.7, quantiles = 4, quantile_lines=T,
                                position = ggridges::position_raincloud(adjust_vlines = T, height=0.1),
  )+
  ggplot2::geom_vline(xintercept=c(10, 15), linetype="dashed", color="red")+
  ggplot2::annotate(geom="text", x=10, y=0.5, label=" 10min", color="red", hjust=1, vjust=1)+
  ggplot2::annotate(geom="text", x=15, y=0.5, label=" 15min", color="red", hjust=0, vjust=1)+
  ggplot2::annotate(geom="text", x=10, y=4.5, label=" 10min", color="red", hjust=1, vjust=1)+
  ggplot2::annotate(geom="text", x=15, y=4.5, label=" 15min", color="red", hjust=0, vjust=1)+
  # ggplot2::theme_bw()
  ggridges::theme_ridges()

# mean and sd per hour
freq <- 60*60
user_trips %>% 
  dplyr::mutate(time_trip = time_wait + time_ride) %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>%
  tidyr::pivot_longer(cols=c(time_trip, time_wait, time_ride)) %>%
  dplyr::group_by(interval, name) %>% 
  dplyr::summarise(
    mean = mean(value, na.rm=T),
    sd = sd(value, na.rm=T),
    # q05 = quantile(value, 0.05, na.rm=T),
    # q25 = quantile(value, 0.25, na.rm=T),
    # q50 = quantile(value, 0.50, na.rm=T),
    # q75 = quantile(value, 0.75, na.rm=T),
    # q95 = quantile(value, 0.95, na.rm=T),
  ) %>% 
  dplyr::ungroup() %>% 
  # tidyr::pivot_longer(-interval) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=mean, color=name))+
  ggplot2::geom_ribbon(ggplot2::aes(x=date, ymin=mean-sd, ymax=mean+sd, fill=name), alpha=0.1, na.rm=T)+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                       ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::theme_bw()
# ggplot2::geom_boxplot(ggplot2::aes(x=factor(date), y=value), size=0.1, outlier.color = NA)+
# ggplot2::facet_grid(rows=dplyr::vars(name), scales="free_y")


# waiting more than 15/30min
freq <- 60*60
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>%
  dplyr::group_by(interval) %>% 
  dplyr::summarise(
    num_users = sum(!is.na(time_wait)),
    waiting_over_10min = sum(time_wait > 10*60, na.rm=T),
    waiting_over_15min = sum(time_wait > 15*60, na.rm=T),
  ) %>% 
  dplyr::ungroup() %>% 
  tidyr::pivot_longer(c(waiting_over_10min, waiting_over_15min)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::theme_bw()


# BIKE DISTRIBUTION -------------------------------------------------------

# no vale
events <- c("charging", "pickup", "rebalancing", "stopped", "use")
fleet_size <- config$NUM_BIKES
freq <- 15*60

num_bikes_use <- user_trips %>% 
  dplyr::mutate(
    time_use_start = ifelse(!is.na(time_ride), time_departure, NA),
    time_use_stop = ifelse(!is.na(time_ride), time_departure + time_ride, NA)
  ) %>% 
  tidyr::pivot_longer(cols=c(time_use_start, time_use_stop), 
                      names_to = "event", values_to="ts") %>% 
  dplyr::select(event, ts)

bike_trips %>% 
  dplyr::mutate(
    time_pickup_start = ifelse(trip_type==1, time_departure, NA),
    time_pickup_stop = ifelse(trip_type==1, time_departure + time_ride, NA),
    time_charging_start = ifelse(trip_type==2, time_departure, NA),
    time_charging_stop = ifelse(trip_type==2, time_departure + time_ride + time_charge, NA),
    time_rebalancing_start = ifelse(trip_type==3, time_departure, NA),
    time_rebalancing_stop = ifelse(trip_type==3, time_departure + time_ride, NA)
  ) %>% 
  tidyr::pivot_longer(cols=c(time_pickup_start, time_pickup_stop,
                             time_charging_start, time_charging_stop,
                             time_rebalancing_start, time_rebalancing_stop), 
                      names_to = "event", values_to="ts") %>% 
  dplyr::select(event, ts) %>% 
  # add num bikes from user_trips
  dplyr::bind_rows(num_bikes_use) %>% 
  # cumulative count per event class
  dplyr::mutate(event_class = stringr::str_match(event, paste0(events, collapse="|"))) %>% 
  dplyr::arrange(ts) %>% 
  dplyr::group_by(event_class) %>% 
  dplyr::mutate(
    increment = stringr::str_ends(event, "start"),
    increment = ifelse(increment, 1, -1),
    count = cumsum(increment)) %>% 
  dplyr::ungroup() %>% 
  dplyr::select(event_class, ts, count) %>% 
  # select maximum from same time and event
  dplyr::group_by(ts, event_class) %>% 
  dplyr::summarise(count = max(count)) %>% 
  dplyr::ungroup() %>% 
  # fill all timestamps with events
  tidyr::complete(event_class, tidyr::nesting(ts)) %>% 
  tidyr::fill(count) %>% 
  dplyr::mutate(count = tidyr::replace_na(count, 0)) %>% 
  na.omit() %>% 
  # calculate stopped
  dplyr::group_by(ts) %>% 
  dplyr::mutate(stopped = fleet_size - sum(count)) %>% 
  dplyr::ungroup() %>% 
  tidyr::pivot_wider(names_from = "event_class", values_from = "count") %>% 
  tidyr::pivot_longer(-ts, names_to = "event_class", values_to = "count") %>% 
  # interval
  dplyr::mutate(interval = floor(ts / freq)) %>%
  dplyr::group_by(interval, event_class) %>% 
  dplyr::summarise(count = mean(count)) %>% 
  dplyr::ungroup() %>% 
  # date variables
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  # ggplot2::geom_area(ggplot2::aes(x=date, y=count, fill=event_class), position="fill")
  ggplot2::geom_line(ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::geom_hline(ggplot2::aes(yintercept = fleet_size), linetype="dashed")

dev.off()
