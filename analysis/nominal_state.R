library(magrittr)

Sys.setlocale("LC_ALL", 'en_US.UTF-8')
Sys.setenv(LANG = "en_US.UTF-8")
extrafont::loadfonts()

origin <- "2019-10-07"
freq_hour <- 60*60
freq_day <- 24*60*60
peak_times <- c(seq(7*60+50, 9*60+30), seq(15*60+50, 18*60+30))
date_breaks <- seq(lubridate::ymd_hm('2019-10-07 12:00'),lubridate::ymd_hm('2019-10-14 12:00'),by='day')
date_minor_breaks <- seq(lubridate::ymd_hm('2019-10-07 00:00'),lubridate::ymd_hm('2019-10-15 00:00'),by='12 hours')

width <- 6
height <- 4

# xticks and xlabels
# color palette NPG

# autonomous charge
# NR: 1000, 2000, 3000
# PR: 1000, 1500, 2000, 3000
# IR: 500, 1000, 2000, 3000


palette <- ggsci::pal_npg()(6)

# STATION_BASED -----------------------------------------------------------

path_SB <- "../results/2021-06-14_16-02-45-station-based/"

config_SB <- jsonlite::fromJSON(file.path(path_SB, "config.json"))
user_trips_SB <- data.table::fread(file.path(path_SB, "user_trips.csv"), na.strings = "None")
bike_trips_SB <- data.table::fread(file.path(path_SB, "bike_trips.csv"), na.strings = "None")

# user state
palette <- ggsci::pal_locuszoom()(3)
palette <- c("#30475E", "#009988", "#EE7733")
events <- c("walking_origin", "riding", "walking_destination")
freq <- 5*60
user_trips_SB %>% 
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
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times,
    peak_start = peak - dplyr::lag(peak) == 1,
    peak_stop = peak - dplyr::lag(peak) == -1,
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak_start | peak_stop) %>% 
                       dplyr::mutate(peak_start = ifelse(peak_start, T, NA), peak_stop = ifelse(peak_stop, T, NA),
                                     date1 = date[peak_start], date2 = date[peak_stop]) %>% 
                       tidyr::fill(date1) %>% dplyr::distinct(date1, date2) %>% na.omit(),
                     ggplot2::aes(xmin=date1, xmax=date2, ymin=-Inf, ymax=Inf), alpha=0.2)+
  ggplot2::geom_path(
    data = . %>% 
      dplyr::mutate(interval = floor(time_departure / freq)) %>% 
      dplyr::group_by(interval, event_class) %>% 
      dplyr::summarise(count = mean(count, na.rm=T)) %>% 
      dplyr::ungroup() %>% 
      dplyr::mutate(ts = interval * freq,
                    date = as.POSIXct(ts, origin = origin, tz = "GMT")),
    ggplot2::aes(x=date, y=count, color=event_class))+
  # ggplot2::geom_point(ggplot2::aes(x=date, y=count, color=event_class), size=0.5)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Riding", "Walking to station", "Walking to destination"))+
  ggplot2::labs(x=NULL, y="Number of People", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.80,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "users_status_SB.pdf", width=width, height=height)


# bike state
fleet_size <- config_SB$NUM_BIKES
palette <- c("#30475E", "#EE7733")
freq <- 5*60
user_trips_SB %>% 
  dplyr::filter(status == "finished") %>% 
  dplyr::mutate(
    time_riding_start = time_departure + time_walk_origin,
    time_riding_stop = time_departure + time_walk_origin + time_ride,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_riding_start, time_riding_stop), names_to = "event", values_to="ts") %>% 
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
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times,
    peak_start = peak - dplyr::lag(peak) == 1,
    peak_stop = peak - dplyr::lag(peak) == -1,
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak_start | peak_stop) %>% 
                       dplyr::mutate(peak_start = ifelse(peak_start, T, NA), peak_stop = ifelse(peak_stop, T, NA),
                                     date1 = date[peak_start], date2 = date[peak_stop]) %>% 
                       tidyr::fill(date1) %>% dplyr::distinct(date1, date2) %>% na.omit(),
                     ggplot2::aes(xmin=date1, xmax=date2, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::geom_hline(ggplot2::aes(yintercept=fleet_size), color="black", linetype="dashed")+
  ggplot2::geom_path(
    data = . %>% 
      dplyr::mutate(interval = floor(time_departure / freq)) %>% 
      dplyr::group_by(interval, event_class) %>% 
      dplyr::summarise(count = mean(count, na.rm=T)) %>% 
      dplyr::ungroup() %>% 
      dplyr::mutate(ts = interval * freq,
                    date = as.POSIXct(ts, origin = origin, tz = "GMT")),
    ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("In Use", "Idle"))+
  ggplot2::labs(x=NULL, y="Number of Bikes", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.73),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "bikes_status_SB.pdf", width=width, height=height)


# trips served/unserved
palette <- c("#30475E", "#EE7733")
freq <- 15*60
user_trips_SB %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    num_trips = dplyr::n(),
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Served", "Unserved"), )+
  ggplot2::labs(x=NULL, y="Number of Trips", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8), 
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "trips_status_SB.pdf", width=width, height=height)


# trips served / unserved filled
freq <- 30*60
palette <- c("#30475E", "#EE7733")
user_trips_SB %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_area(ggplot2::aes(x=date, y=value, fill=name), 
                     color=NA, position=ggplot2::position_fill(reverse=T))+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.03)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_y_continuous(breaks=seq(0,1,by=0.2))+
  ggplot2::scale_fill_manual(values=palette, labels=c("Served", "Unserved"), )+
  ggplot2::labs(x=NULL, y="Ratio of Trips", fill="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.18),
    # legend.position = "none",
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),    
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "trips_status_fill_SB.pdf", width=width, height=height)


# time ride, etc

# mean and sd per hour
freq <- 60*60
palette <- c("#EE7733", "#CC3311", "#AA4499", "#009988")
user_trips_SB %>% 
  dplyr::mutate(time_trip = time_walk_origin + time_ride + time_walk_destination) %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>%
  tidyr::pivot_longer(cols=c(time_trip, time_walk_origin, time_ride, time_walk_destination)) %>%
  dplyr::group_by(interval, name) %>% 
  dplyr::summarise(
    value = value / 60,
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
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak) %>% dplyr::distinct(date),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_y_continuous(limits=c(0, NA))+
  ggplot2::scale_fill_manual(values=palette, labels=c("Ride", "Trip", "Walk to destination", "Walk to station"), )+
  ggplot2::scale_color_manual(values=palette, labels=c("Ride", "Trip", "Walk to destination", "Walk to station"), )+
  ggplot2::labs(x=NULL, y="Time [min]", color="Time", fill="Time")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.80,0.76),
    # legend.position = "none",
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),     
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "times_distribution_SB.pdf", width=width, height=height)




# DOCKLESS ----------------------------------------------------------------


path_DK <- "../results/2021-06-14_16-34-20-dockless/"

config_DK <- jsonlite::fromJSON(file.path(path_DK, "config.json"))
user_trips_DK <- data.table::fread(file.path(path_DK, "user_trips.csv"), na.strings = "None")
bike_trips_DK <- data.table::fread(file.path(path_DK, "bike_trips.csv"), na.strings = "None")

# user state
events <- c("walking", "riding")
palette <- c("#30475E", "#EE7733")
freq <- 5*60
user_trips_DK %>% 
  dplyr::filter(!is.na(time_ride)) %>% 
  dplyr::mutate(
    time_walking_start = time_departure,
    time_walking_stop = time_departure + time_walk_origin,
    time_riding_start = time_departure + time_walk_origin,
    time_riding_stop = time_departure + time_walk_origin + time_ride,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_walking_start, time_walking_stop,
                             time_riding_start, time_riding_stop),
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
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times,
    peak_start = peak - dplyr::lag(peak) == 1,
    peak_stop = peak - dplyr::lag(peak) == -1,
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak_start | peak_stop) %>% 
                       dplyr::mutate(peak_start = ifelse(peak_start, T, NA), peak_stop = ifelse(peak_stop, T, NA),
                                     date1 = date[peak_start], date2 = date[peak_stop]) %>% 
                       tidyr::fill(date1) %>% dplyr::distinct(date1, date2) %>% na.omit(),
                     ggplot2::aes(xmin=date1, xmax=date2, ymin=-Inf, ymax=Inf), alpha=0.2)+
  ggplot2::geom_path(
    data = . %>% 
      dplyr::mutate(interval = floor(time_departure / freq)) %>% 
      dplyr::group_by(interval, event_class) %>% 
      dplyr::summarise(count = mean(count, na.rm=T)) %>% 
      dplyr::ungroup() %>% 
      dplyr::mutate(ts = interval * freq,
                    date = as.POSIXct(ts, origin = origin, tz = "GMT")),
    ggplot2::aes(x=date, y=count, color=event_class))+
  # ggplot2::geom_point(ggplot2::aes(x=date, y=count, color=event_class), size=0.5)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Riding", "Walking"))+
  ggplot2::labs(x=NULL, y="Number of People", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.80,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),   
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "users_status_DK.pdf", width=width, height=height)


# bike state
fleet_size <- config_DK$NUM_BIKES
palette <- c("#30475E", "#EE7733")
freq <- 5*60
user_trips_DK %>% 
  dplyr::filter(!is.na(time_ride)) %>% 
  dplyr::mutate(
    time_riding_start = time_departure + time_walk_origin,
    time_riding_stop = time_departure + time_walk_origin + time_ride,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_riding_start, time_riding_stop), names_to = "event", values_to="ts") %>% 
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
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times,
    peak_start = peak - dplyr::lag(peak) == 1,
    peak_stop = peak - dplyr::lag(peak) == -1,
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak_start | peak_stop) %>% 
                       dplyr::mutate(peak_start = ifelse(peak_start, T, NA), peak_stop = ifelse(peak_stop, T, NA),
                                     date1 = date[peak_start], date2 = date[peak_stop]) %>% 
                       tidyr::fill(date1) %>% dplyr::distinct(date1, date2) %>% na.omit(),
                     ggplot2::aes(xmin=date1, xmax=date2, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::geom_hline(ggplot2::aes(yintercept=fleet_size), color="black", linetype="dashed")+
  ggplot2::geom_path(
    data = . %>% 
      dplyr::mutate(interval = floor(time_departure / freq)) %>% 
      dplyr::group_by(interval, event_class) %>% 
      dplyr::summarise(count = mean(count, na.rm=T)) %>% 
      dplyr::ungroup() %>% 
      dplyr::mutate(ts = interval * freq,
                    date = as.POSIXct(ts, origin = origin, tz = "GMT")),
    ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("In Use", "Idle"))+
  ggplot2::labs(x=NULL, y="Number of Bikes", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.73),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),    
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "bikes_status_DK.pdf", width=width, height=height)



# trips served/unserved
freq <- 15*60
palette <- c("#30475E", "#EE7733")
user_trips_DK %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    num_trips = dplyr::n(),
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Served", "Unserved"), )+
  ggplot2::labs(x=NULL, y="Number of Trips", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),    
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "trips_status_DK.pdf", width=width, height=height)


# trips served / unserved filled
freq <- 30*60
palette <- c("#30475E", "#EE7733")
user_trips_DK %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_area(ggplot2::aes(x=date, y=value, fill=name), 
                     color=NA, position=ggplot2::position_fill(reverse=T))+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.03)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_y_continuous(breaks=seq(0,1,by=0.2))+
  ggplot2::scale_fill_manual(values=palette, labels=c("Served", "Unserved"), )+
  ggplot2::labs(x=NULL, y="Ratio of Trips", fill="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.18),
    # legend.position = "none",
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),    
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "trips_status_fill_DK.pdf", width=width, height=height)


# time ride, etc

# mean and sd per hour
freq <- 60*60
palette <- c("#EE7733", "#CC3311", "#AA4499", "#009988")
user_trips_DK %>% 
  dplyr::mutate(time_trip = time_walk_origin + time_ride) %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>%
  tidyr::pivot_longer(cols=c(time_trip, time_walk_origin, time_ride)) %>%
  dplyr::group_by(interval, name) %>% 
  dplyr::summarise(
    value = value / 60,
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
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak) %>% dplyr::distinct(date),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_y_continuous(limits=c(0, NA))+
  ggplot2::scale_fill_manual(values=palette, labels=c("Ride", "Trip", "Walk to bike"), )+
  ggplot2::scale_color_manual(values=palette, labels=c("Ride", "Trip", "Walk to bike"), )+
  ggplot2::labs(x=NULL, y="Time [min]", color="Time", fill="Time")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.80,0.76),
    # legend.position = "none",
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),     
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "times_distribution_DK.pdf", width=width, height=height)



# AUTONOMOUS --------------------------------------------------------------


path_AU <- "../results/2021-06-14_16-56-43-autonomous/"

config_AU <- jsonlite::fromJSON(file.path(path_AU, "config.json"))
user_trips_AU <- data.table::fread(file.path(path_AU, "user_trips.csv"), na.strings = "None")
bike_trips_AU <- data.table::fread(file.path(path_AU, "bike_trips.csv"), na.strings = "None")

# user state
events <- c("wait", "riding")
palette <- c("#30475E", "#EE7733")
freq <- 5*60
user_trips_AU %>% 
  dplyr::filter(!is.na(time_ride)) %>% 
  dplyr::mutate(
    time_wait_start = time_departure,
    time_wait_stop = time_departure + time_wait,
    time_riding_start = time_departure + time_wait,
    time_riding_stop = time_departure + time_wait + time_ride,
  ) %>% 
  tidyr::pivot_longer(cols=c(time_wait_start, time_wait_stop,
                             time_riding_start, time_riding_stop),
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
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times,
    peak_start = peak - dplyr::lag(peak) == 1,
    peak_stop = peak - dplyr::lag(peak) == -1,
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak_start | peak_stop) %>% 
                       dplyr::mutate(peak_start = ifelse(peak_start, T, NA), peak_stop = ifelse(peak_stop, T, NA),
                                     date1 = date[peak_start], date2 = date[peak_stop]) %>% 
                       tidyr::fill(date1) %>% dplyr::distinct(date1, date2) %>% na.omit(),
                     ggplot2::aes(xmin=date1, xmax=date2, ymin=-Inf, ymax=Inf), alpha=0.2)+
  ggplot2::geom_path(
    data = . %>% 
      dplyr::mutate(interval = floor(time_departure / freq)) %>% 
      dplyr::group_by(interval, event_class) %>% 
      dplyr::summarise(count = mean(count, na.rm=T)) %>% 
      dplyr::ungroup() %>% 
      dplyr::mutate(ts = interval * freq,
                    date = as.POSIXct(ts, origin = origin, tz = "GMT")),
    ggplot2::aes(x=date, y=count, color=event_class))+
  # ggplot2::geom_point(ggplot2::aes(x=date, y=count, color=event_class), size=0.5)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Riding", "Waiting"))+
  ggplot2::labs(x=NULL, y="Number of Trips", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.80,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),   
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "users_status_AU.pdf", width=width, height=height)


# bike state

# no vale
events <- c("charging", "pickup", "rebalancing", "stopped", "use")
fleet_size <- config_AU$NUM_BIKES
freq <- 5*60

num_bikes_use <- user_trips_AU %>% 
  dplyr::mutate(
    time_use_start = ifelse(!is.na(time_ride), time_departure, NA),
    time_use_stop = ifelse(!is.na(time_ride), time_departure + time_ride, NA)
  ) %>% 
  tidyr::pivot_longer(cols=c(time_use_start, time_use_stop), 
                      names_to = "event", values_to="ts") %>% 
  dplyr::select(event, ts)

palette <- c("#CC3311", "#009988", "#AA4499", "#EE7733", "#30475E")
bike_trips_AU %>% 
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
    peak = time %in% peak_times,
    peak_start = peak - dplyr::lag(peak) == 1,
    peak_stop = peak - dplyr::lag(peak) == -1,
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak_start | peak_stop) %>% 
                       dplyr::mutate(peak_start = ifelse(peak_start, T, NA), peak_stop = ifelse(peak_stop, T, NA),
                                     date1 = date[peak_start], date2 = date[peak_stop]) %>% 
                       tidyr::fill(date1) %>% dplyr::distinct(date1, date2) %>% na.omit(),
                     ggplot2::aes(xmin=date1, xmax=date2, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::geom_hline(ggplot2::aes(yintercept=fleet_size), color="black", linetype="dashed")+
  ggplot2::geom_line(ggplot2::aes(x=date, y=count, color=event_class))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Charging", "Pickup", "Rebalancing", "Idle", "In Use"))+
  ggplot2::labs(x=NULL, y="Number of Bikes", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.47),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),    
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "bikes_status_AU.pdf", width=width, height=height)



# trips served/unserved
freq <- 15*60
palette <- c("#30475E", "#EE7733")
user_trips_AU %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    num_trips = dplyr::n(),
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::geom_line(ggplot2::aes(x=date, y=value, color=name))+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_color_manual(values=palette, labels=c("Served", "Unserved"), )+
  ggplot2::labs(x=NULL, y="Number of Trips", color="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.76),
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),    
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "trips_status_AU.pdf", width=width, height=height)


# trips served / unserved filled
freq <- 30*60
palette <- c("#30475E", "#EE7733")
user_trips_AU %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  dplyr::group_by(interval) %>% 
  dplyr::summarize(
    served_trips = sum(!is.na(time_ride)),
    unserved_trips = sum(is.na(time_ride))
  ) %>%
  tidyr::pivot_longer(cols = c(served_trips, unserved_trips)) %>% 
  dplyr::mutate(
    ts = interval * freq,
    date = as.POSIXct(ts, origin = origin, tz = "GMT"),
    time = lubridate::hour(date)*60 + lubridate::minute(date),
    peak = time %in% peak_times
  ) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_area(ggplot2::aes(x=date, y=value, fill=name), 
                     color=NA, position=ggplot2::position_fill(reverse=T))+
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.03)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_y_continuous(breaks=seq(0,1,by=0.2))+
  ggplot2::scale_fill_manual(values=palette, labels=c("Served", "Unserved"), )+
  ggplot2::labs(x=NULL, y="Ratio of Trips", fill="Legend")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.85,0.18),
    # legend.position = "none",
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),  
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "trips_status_fill_AU.pdf", width=width, height=height)


# time ride, etc

# mean and sd per hour
freq <- 60*60
palette <- c("#EE7733", "#CC3311", "#AA4499", "#009988")
user_trips_AU %>% 
  dplyr::mutate(time_trip = time_wait + time_ride) %>% 
  dplyr::mutate(interval = floor(time_departure / freq)) %>% 
  tidyr::pivot_longer(cols=c(time_trip, time_wait, time_ride)) %>%
  dplyr::group_by(interval, name) %>% 
  dplyr::summarise(
    value = value / 60,
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
  ggplot2::geom_rect(data = . %>% dplyr::filter(peak) %>% dplyr::distinct(date),
                     ggplot2::aes(xmin=date, xmax=date+freq, ymin=-Inf, ymax=Inf), alpha=0.1)+
  ggplot2::scale_x_datetime(date_labels = "%A", breaks = date_breaks, minor_breaks = date_minor_breaks)+
  ggplot2::scale_y_continuous(limits=c(0, NA))+
  ggplot2::scale_fill_manual(values=palette, labels=c("Ride", "Trip", "Wait"), )+
  ggplot2::scale_color_manual(values=palette, labels=c("Ride", "Trip", "Wait"), )+
  ggplot2::labs(x=NULL, y="Time [min]", color="Time", fill="Time")+
  hrbrthemes::theme_ipsum(base_family = "Ubuntu", axis_title_just = "c")+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.position = c(0.80,0.76),
    # legend.position = "none",
    legend.background = ggplot2::element_rect(fill = "white", colour = NA),
    axis.title.x = ggplot2::element_text(size=10),
    axis.text.x = ggplot2::element_text(size=8),
    axis.title.y = ggplot2::element_text(size=10),
    axis.text.y = ggplot2::element_text(size=8),   
    panel.grid.major.x = ggplot2::element_blank(),
  )+
  ggplot2::ggsave(filename = "times_distribution_AU.pdf", width=width, height=height)
