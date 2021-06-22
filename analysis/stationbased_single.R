library(magrittr)
Sys.setlocale("LC_ALL", 'en_US.UTF-8')
Sys.setenv(LANG = "en_US.UTF-8")

# path_experiments <- "../results/station-based-23-03-2021/"
# path_dir <- list.files(path_experiments, full.names = T)

path <- "../results/2021-04-02_17-46-44/"
path <- "../results/station-based-03-04-2021/2021-04-02_18-20-43/"

config <- jsonlite::fromJSON(file.path(path, "config.json"))
user_trips <- data.table::fread(file.path(path, "user_trips.csv"), na.strings = "None")
bike_trips <- data.table::fread(file.path(path, "bike_trips.csv"), na.strings = "None")


pdf("output.pdf", width = 12, height=8)

# NUMBER MAGIC BIKES / DOCKS -----------------------------------------------

bike_trips %>% nrow
(user_trips$magic_bike %>% sum) + (user_trips$magic_dock %>% sum)

bike_trips$magic_bike %>% sum
user_trips$magic_bike %>% sum

bike_trips$magic_dock %>% sum
user_trips$magic_dock %>% sum

# DEMAND ------------------------------------------------------------------

origin <- "2019-10-07"
freq <- 30*60
freq_hour <- 60*60
freq_day <- 24*60*60
date_breaks <- seq(lubridate::ymd_hm('2019-10-07 12:00'),lubridate::ymd_hm('2019-10-14 12:00'),by='day')
date_minor_breaks <- seq(lubridate::ymd_hm('2019-10-07 00:00'),lubridate::ymd_hm('2019-10-15 00:00'),by='12 hours')


width <- 6
height <- 4

# demand along the week
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::mutate(count = dplyr::n()) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT")
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=count))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  # ggplot2::ggtitle(paste0("Demand: trip count every ", freq/60, " minutes"))+
  ggplot2::labs(x=NULL, y="Number of Trips", color="Weekday")+
  # ggplot2::theme_bw()+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.9,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "demand_1.pdf", width=width, height=height)

# demand per day
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::mutate(count = dplyr::n()) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date_day, y=count, color=day), size=0.5)+
  ggplot2::scale_x_datetime(date_labels = "%H:%M", date_breaks = "2 hours")+
  ggsci::scale_color_locuszoom()+
  # ggplot2::ggtitle(paste0("Demand: trip count every ", freq/60, " minutes, per day"))+
  ggplot2::labs(x="Time [HH:MM]", y="Number of Trips", color="Weekday")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.9,0.73),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),
    )+
  ggplot2::ggsave(filename = "demand_2.pdf", width=width, height=height)


# demand air distance
deg2rad <- function(deg) return(deg*pi/180)
haversine <- function(lon1, lat1, lon2, lat2) {
  R <- 6371000 # Earth mean radius [m]
  d <- acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2) * cos(lon2-lon1)) * R
  return(d) # Distance in m
}

# trip air distance: density plot
user_trips %>%
  dplyr::mutate(
    trip_air_distance = haversine(deg2rad(origin_lon), deg2rad(origin_lat),
                                  deg2rad(destination_lon), deg2rad(destination_lat)),
  ) %>%
  ggplot2::ggplot()+
  ggplot2::geom_density(ggplot2::aes(x=trip_air_distance), na.rm=T)+
  ggplot2::geom_vline(ggplot2::aes(xintercept = mean(trip_air_distance)), linetype="dashed", color="red")+
  ggplot2::ggtitle("Demand: trip air-distance")+
  ggplot2::theme_bw()

# trip air distance: boxplot
user_trips %>% 
  dplyr::mutate(
    trip_air_distance = haversine(deg2rad(origin_lon), deg2rad(origin_lat), 
                                  deg2rad(destination_lon), deg2rad(destination_lat)),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_boxplot(ggplot2::aes(y=trip_air_distance), na.rm=T)+
  ggplot2::geom_hline(ggplot2::aes(yintercept = mean(trip_air_distance)), linetype="dashed", color="red")+
  ggplot2::ggtitle("Demand: trip air-distance")+
  ggplot2::theme_bw()


# trip air distance: boxplot by distance
breaks <- seq(0, 15000, by=1000)
labels <- mapply(paste0, breaks/1000, "-", breaks[-1]/1000, " km")[-1]
user_trips %>% 
  dplyr::mutate(
    trip_air_distance = haversine(deg2rad(origin_lon), deg2rad(origin_lat), 
                                  deg2rad(destination_lon), deg2rad(destination_lat)),
    trip_air_distance = cut(trip_air_distance, breaks, labels)
  ) %>% 
  dplyr::count(trip_air_distance) %>% 
  na.omit() %>% 
  dplyr::mutate(
    n_cumsum = cumsum(n),
    n_cumsum = n_cumsum / max(n_cumsum),
    g = 1
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_col(ggplot2::aes(x=trip_air_distance, y=n, color = "Number_of_Trips"), width=0.7, fill="#343A40", na.rm=T)+
  ggplot2::geom_line(ggplot2::aes(x=trip_air_distance, y=n_cumsum*25000, group=g, color="Cumulative_Distribution"),
                     size=1, linetype="solid", na.rm=T)+
  ggplot2::geom_point(ggplot2::aes(x=trip_air_distance, y=n_cumsum*25000, color="Cumulative_Distribution"),
                     size=2, shape=15, na.rm=T)+
  ggplot2::scale_y_continuous(
    sec.axis = ggplot2::sec_axis(trans = ~ ./250, name = "Cumulative Distribution [%]", breaks = seq(0,100,by=10), )
  )+
  ggplot2::scale_color_manual(labels = c("Cumulative Distribution [%]","Number of Trips"), 
                              values = c("#01937C", "#343A40"))+
  ggplot2::guides(color = ggplot2::guide_legend(override.aes = list(fill = "white"))) +
  # ggplot2::ggtitle("Demand: trip air-distance, by km")+
  ggplot2::theme_bw()+
  ggplot2::labs(x="Trip Air Distance [km]", y="Number of Trips", color=NULL)+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.78,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),
  )+
  ggplot2::ggsave(filename = "demand_3.pdf", width=width, height=height)

# trips status: boxplot by distance, colored by status
user_trips %>% 
  dplyr::mutate(
    trip_air_distance = haversine(deg2rad(origin_lon), deg2rad(origin_lat), 
                                  deg2rad(destination_lon), deg2rad(destination_lat)),
    trip_air_distance = cut(trip_air_distance, breaks, labels)
  ) %>% 
  dplyr::count(trip_air_distance, status) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_col(ggplot2::aes(x=trip_air_distance, y=n, fill=status), position="stack", na.rm=T)+
  ggplot2::ggtitle("Trips status: by trip air-distance")+
  ggplot2::theme_bw()


# trip air distance: boxplot by hour
user_trips %>% 
  dplyr::mutate(
    trip_air_distance = haversine(deg2rad(origin_lon), deg2rad(origin_lat), 
                                  deg2rad(destination_lon), deg2rad(destination_lat)),
    day_hour = floor(time_departure / freq_hour) %% 24,
  ) %>% 
  dplyr::group_by(day_hour) %>% 
  dplyr::mutate(mean_trip_air_distance = mean(trip_air_distance)) %>% 
  dplyr::ungroup() %>% 
  ggplot2::ggplot()+
  ggplot2::geom_boxplot(ggplot2::aes(x=factor(day_hour), y=trip_air_distance), na.rm=T, outlier.alpha = 0.1)+
  ggplot2::geom_point(ggplot2::aes(x=factor(day_hour), y=mean_trip_air_distance), color="red")+
  ggplot2::ggtitle("Demand: trip air-distance, by hour")+
  ggplot2::theme_bw()


# TRIPS ----------------------------------------------------------

# trips by status, by interval along the week
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval,status) %>% 
  dplyr::mutate(count = dplyr::n()) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=count, color=status))+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hours")+
  ggplot2::ggtitle(paste0("Trips status: count every ", freq/60, " minutes"))+
  ggplot2::theme_bw()

# trips by status, by interval along the week
user_trips %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval, status) %>% 
  dplyr::mutate(count = dplyr::n()) %>% 
  dplyr::ungroup() %>% 
  dplyr::group_by(interval) %>% 
  dplyr::mutate(count_rel = count / sum(count)) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_col(ggplot2::aes(x=date, y=count_rel, fill=status),
                    position="stack", color=NA, width=freq, na.rm=T)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hours")+
  ggplot2::ggtitle(paste0("Trips status: stacked count every ", freq/60, " minutes"))+
  ggplot2::theme_bw()

# trips by status, by discrete events along the week
user_trips %>% 
  # dplyr:filter(status == "finished") %>%
  dplyr::mutate(
    time_finish = time_departure + time_walk_origin + time_ride + time_walk_destination
  ) %>% 
  tidyr::pivot_longer(cols=c(time_departure, time_finish), names_to = "event", values_to="ts") %>% 
  dplyr::arrange(ts) %>% 
  dplyr::group_by(status) %>% 
  dplyr::mutate(
    increment = ifelse(event == "time_departure", 1, -1),
    count = cumsum(increment)) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=date, y=count, color=status), na.rm=T)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::ggtitle("Trips status: count every discrete event")+
  ggplot2::theme_bw()


# num people riding/walking, by discrete event
events <- c("walking_origin", "riding", "walking_destination")
events <- c("walking", "riding", "walking")
user_trips %>% 
  dplyr::filter(status == "finished") %>% 
  dplyr::mutate(
    time_walking_origin_start = time_departure,
    time_walking_origin_stop = time_departure + time_walk_origin,
    time_riding_start = time_departure + time_walk_origin,
    time_riding_stop = time_departure + time_walk_origin + time_ride,
    time_walking_destination_start = time_departure + time_walk_origin + time_ride,
    time_walking_destination_stop = time_departure + time_walk_origin + time_ride + time_walk_destination,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_walking_origin_start, time_walking_origin_stop,
                             time_riding_start, time_riding_stop,
                             time_walking_destination_start, time_walking_destination_stop), 
                      names_to = "event", values_to="ts") %>% 
  dplyr::mutate(event_class = stringr::str_match(event, paste0(events, collapse="|"))) %>% 
  dplyr::arrange(ts) %>%
  dplyr::group_by(event_class) %>% 
  dplyr::mutate(
    increment = stringr::str_ends(event, "start"),
    increment = ifelse(increment, 1, -1),
    count = cumsum(increment)) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_path(ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::ggtitle("Trips activities: by discrete events")+
  ggplot2::theme_bw()


# num people riding/walking, by frequency
freq <- 60*60
user_trips %>% 
  dplyr::filter(status == "finished") %>% 
  dplyr::mutate(
    time_walking_origin_start = time_departure,
    time_walking_origin_stop = time_departure + time_walk_origin,
    time_riding_start = time_departure + time_walk_origin,
    time_riding_stop = time_departure + time_walk_origin + time_ride,
    time_walking_destination_start = time_departure + time_walk_origin + time_ride,
    time_walking_destination_stop = time_departure + time_walk_origin + time_ride + time_walk_destination,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_walking_origin_start, time_walking_origin_stop,
                             time_riding_start, time_riding_stop,
                             time_walking_destination_start, time_walking_destination_stop), 
                      names_to = "event", values_to="ts") %>% 
  dplyr::mutate(event_class = stringr::str_match(event, paste0(events, collapse="|"))) %>% 
  dplyr::arrange(ts) %>%
  dplyr::group_by(event_class) %>% 
  dplyr::mutate(
    increment = stringr::str_ends(event, "start"),
    increment = ifelse(increment, 1, -1),
    count = cumsum(increment)) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(interval = floor(ts / freq)) %>% 
  dplyr::group_by(interval, event_class) %>% 
  dplyr::summarise(count_interval = sum(count)) %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_col(ggplot2::aes(x=date, y=count_interval, fill=event_class),
                    position="fill", width=freq)+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::ggtitle(paste0("Trips activities: by ", freq/60, " minutes"))+
  ggplot2::theme_bw()



# num bikes stopped / riding
fleet_size <- config$NUM_BIKES
user_trips %>% 
  dplyr::filter(status == "finished") %>% 
  dplyr::mutate(
    time_riding_start = time_departure + time_walk_origin,
    time_riding_stop = time_departure + time_walk_origin + time_ride,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_riding_start, time_riding_stop),
                      names_to = "event", values_to="ts") %>% 
  dplyr::arrange(ts) %>%
  dplyr::mutate(
    increment = stringr::str_ends(event, "start"),
    increment = ifelse(increment, 1, -1),
    riding = cumsum(increment),
    stopped = fleet_size - riding) %>% 
  tidyr::pivot_longer(cols=c(riding, stopped), names_to = "event_class", values_to="count") %>% 
  dplyr::mutate(
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    day = lubridate::wday(date, label=T, locale='en_US.UTF-8', week_start = 1),
    date_day = hms::as_hms(date) %>% as.POSIXct(origin=origin),
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_path(ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::scale_x_datetime(date_labels = "%d-%m-%Y", date_breaks = "1 day", date_minor_breaks = "1 hour")+
  ggplot2::ggtitle("Bikes activities: by discrete events")+
  ggplot2::theme_bw()



dev.off()