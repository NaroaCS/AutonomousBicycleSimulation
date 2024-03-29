library(magrittr)
Sys.setlocale("LC_ALL", 'en_US.UTF-8')
Sys.setenv(LANG = "en_US.UTF-8")
extrafont::loadfonts()

path_experiments <- "../results/station-based-03-04-2021/"
path_dir <- list.files(path_experiments, full.names = T)
path <- path_dir[1]

process <- function(path){
  
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
    magic_min_bikes = config$MAGIC_MIN_BIKES, # [-]
    magic_min_docks = config$MAGIC_MIN_DOCKS, # [-]
    user_trips_file = config$USER_TRIPS_FILE # [-]
  )
  
  
  # DATES -------------------------------------------------------------------
  
  origin <- "2019-10-07"
  freq_hour <- 60*60
  freq_day <- 24*60*60
  peak_times <- c(seq(7*60+50, 9*60+30), seq(15*60+50, 18*60+30))
  
  # ABSOLUTE VALUES ---------------------------------------------------------
  

  user_trips %>% 
    dplyr::mutate(time_departure = as.numeric(time_departure)) %>% 
    # CONFIG
    merge(df_config) %>% 
    dplyr::summarise(
      # CONFIG
      mode = mode, # []
      num_bikes = num_bikes, # []
      walk_radius = walk_radius, # [m]
      riding_speed = riding_speed, # [km/h]
      walking_speed = walking_speed, # [km/h]
      magic_beta = magic_beta, # [%]
      magic_min_bikes = magic_min_bikes, # [-]
      magic_min_docks = magic_min_docks, # [-]
      user_trips_file = user_trips_file, # [-]
      
      # VEHICLES
      time_total = diff(range(time_departure, na.rm=T))*num_bikes, # [s]
      time_total.bike = time_total / num_bikes, # [s/bike]
      
      time_in_use = sum(time_ride, na.rm=T), # [s]
      vkt_in_use = time_in_use * config$RIDING_SPEED / 3.6 / 1000, # [km]
      
      # USERS
      num_users = dplyr::n(), # []
      time_walk_origin_avg = mean(time_walk_origin, na.rm=T), # [s]
      time_walk_destination_avg = mean(time_walk_destination, na.rm=T), # [s]
      time_ride_avg = mean(time_ride, na.rm=T), # [s]
      time_trip_avg = mean(time_walk_origin + time_ride + time_walk_destination, na.rm=T), # [s]
      
      walk_over_10min_origin = sum(time_walk_origin > 10*60, na.rm=T), # []
      walk_over_15min_origin = sum(time_walk_origin > 15*60, na.rm=T), # []
      walk_over_10min_origin.user = walk_over_10min_origin/num_users * 100, # [%]
      walk_over_15min_origin.user = walk_over_15min_origin/num_users * 100, # [%]
      
      walk_over_10min_destination = sum(time_walk_destination > 10*60, na.rm=T), # []
      walk_over_15min_destination = sum(time_walk_destination > 15*60, na.rm=T), # []
      walk_over_10min_destination.user = walk_over_10min_destination/num_users * 100, # [%]
      walk_over_15min_destination.user = walk_over_15min_destination/num_users * 100, # [%]
      
      num_stations_visited_origin = mean(stringr::str_count(origin_visited_stations %>% na.omit(), ";")+1, na.rm=T),
      num_stations_visited_destination = mean(stringr::str_count(destination_visited_stations %>% na.omit(), ";")+1, na.rm=T),
      
      
      # TRIPS
      num_trips = dplyr::n(), # []
      served_trips = sum(status == "finished", na.rm=T), # []
      served_trips.total = served_trips / num_trips * 100, # [%]
      # served_trips = sum(!is.na(time_ride)), # []
      unserved_trips_no_walkable_stations = sum(status == "not_walkable_stations", na.rm=T), # []
      unserved_trips_no_bikes = sum(status == "no_bikes", na.rm=T), # []
      unserved_trips = num_trips - served_trips, # []
      unserved_trips.total = unserved_trips / num_trips * 100, # [%]
      
      num_magic_bikes = sum(magic_bike, na.rm=T), # []
      num_magic_docks = sum(magic_dock, na.rm=T), # []
      num_magic = num_magic_bikes + num_magic_docks, # []
      
      # EXTRA VEHICLES
      num_days = time_total.bike / (60 * 60 * 24), # [day]
      num_trips_bike_day = served_trips / num_bikes / num_days, # []
      
      num_used_bikes = length(unique(bike_id)),
      num_trips_bike_in_use_day = served_trips / num_used_bikes / num_days, # []
      
      num_bikes_in_use = num_used_bikes,
      num_bikes_in_use.total = num_used_bikes / num_bikes * 100,
      num_bikes_stopped = num_bikes - num_used_bikes,
      num_bikes_stopped.total = num_bikes_stopped / num_bikes * 100 ,
      
      .groups = "keep"
    ) %>% 
    dplyr::distinct() %>% 
    dplyr::mutate(
      
      vkt_total = vkt_in_use,
      vkt_total.bike = vkt_total / num_bikes,
      
      vkt_in_use.bike = vkt_in_use / num_bikes, # [km/bike]
      vkt_in_use.dist = vkt_in_use / vkt_total * 100, # [%]
      
      time_stop = time_total - time_in_use, # [s]
      
      time_in_use.bike = time_in_use / num_bikes, # [s/bike]
      time_in_use.time = time_in_use / time_total * 100, # [%]
      
      time_stop.bike = time_stop / num_bikes, # [s/bike]
      time_stop.time = time_stop / time_total * 100, # [%]
      
    ) %>% 
    tibble::rowid_to_column("interval") %>% 
    dplyr::mutate(interval = NA) -> total
  # t %>% as.data.frame %>% tibble::rownames_to_column() %>% `colnames<-`(c("variable", "value"))
  
  # return(total)
  # PER HOUR
  
  freq <- 60*60
  bikes_id <- seq(config$NUM_BIKES)-1
  
  user_trips %>% 
    dplyr::mutate(time_departure = as.numeric(time_departure)) %>% 
    # CONFIG
    merge(df_config) %>% 
    dplyr::mutate(
      time = time_departure,
      interval = floor(time / freq),
    ) %>% 
    dplyr::group_by(interval) %>% 
    dplyr::summarise(
      # CONFIG
      mode = mode, # []
      num_bikes = num_bikes, # []
      walk_radius = walk_radius, # [m]
      riding_speed = riding_speed, # [km/h]
      walking_speed = walking_speed, # [km/h]
      magic_beta = magic_beta, # [%]
      magic_min_bikes = magic_min_bikes, # [-]
      magic_min_docks = magic_min_docks, # [-]
      user_trips_file = user_trips_file, # [-]
      
      # VEHICLES
      time_total = diff(range(time_departure, na.rm=T))*num_bikes, # [s]
      time_total.bike = time_total / num_bikes, # [s/bike]
      
      time_in_use = sum(time_ride, na.rm=T), # [s]
      vkt_in_use = time_in_use * config$RIDING_SPEED / 3.6 / 1000, # [km]
      
      # USERS
      num_users = dplyr::n(), # []
      time_walk_origin_avg = mean(time_walk_origin, na.rm=T), # [s]
      time_walk_destination_avg = mean(time_walk_destination, na.rm=T), # [s]
      time_ride_avg = mean(time_ride, na.rm=T), # [s]
      time_trip_avg = mean(time_walk_origin + time_ride + time_walk_destination, na.rm=T), # [s]
      
      walk_over_10min_origin = sum(time_walk_origin > 10*60, na.rm=T), # []
      walk_over_15min_origin = sum(time_walk_origin > 15*60, na.rm=T), # []
      walk_over_10min_origin.user = walk_over_10min_origin/num_users * 100, # [%]
      walk_over_15min_origin.user = walk_over_15min_origin/num_users * 100, # [%]
      
      walk_over_10min_destination = sum(time_walk_destination > 10*60, na.rm=T), # []
      walk_over_15min_destination = sum(time_walk_destination > 15*60, na.rm=T), # []
      walk_over_10min_destination.user = walk_over_10min_destination/num_users * 100, # [%]
      walk_over_15min_destination.user = walk_over_15min_destination/num_users * 100, # [%]
      
      num_stations_visited_origin = mean(stringr::str_count(origin_visited_stations %>% na.omit(), ";")+1, na.rm=T),
      num_stations_visited_destination = mean(stringr::str_count(destination_visited_stations %>% na.omit(), ";")+1, na.rm=T),
      
      
      # TRIPS
      num_trips = dplyr::n(), # []
      served_trips = sum(status == "finished", na.rm=T), # []
      served_trips.total = served_trips / num_trips * 100, # [%]
      # served_trips = sum(!is.na(time_ride)), # []
      unserved_trips_no_walkable_stations = sum(status == "not_walkable_stations", na.rm=T), # []
      unserved_trips_no_bikes = sum(status == "no_bikes", na.rm=T), # []
      unserved_trips = num_trips - served_trips, # []
      unserved_trips.total = unserved_trips / num_trips * 100, # [%]
      
      num_magic_bikes = sum(magic_bike, na.rm=T), # []
      num_magic_docks = sum(magic_dock, na.rm=T), # []
      num_magic = num_magic_bikes + num_magic_docks, # []
      
      # EXTRA VEHICLES
      num_days = time_total.bike / (60 * 60 * 24), # [day]
      num_trips_bike_day = served_trips / num_bikes / num_days, # []
      
      num_used_bikes = length(unique(bike_id)),
      num_trips_bike_in_use_day = served_trips / num_used_bikes / num_days, # []
      
      num_bikes_in_use = num_used_bikes,
      num_bikes_in_use.total = num_used_bikes / num_bikes * 100,
      num_bikes_stopped = num_bikes - num_used_bikes,
      num_bikes_stopped.total = num_bikes_stopped / num_bikes * 100 ,
      
      .groups = "keep"
    ) %>% 
    dplyr::ungroup() %>% 
    dplyr::distinct() %>% 
    dplyr::mutate(
      
      vkt_total = vkt_in_use,
      vkt_total.bike = vkt_total / num_bikes,
      
      vkt_in_use.bike = vkt_in_use / num_bikes, # [km/bike]
      vkt_in_use.dist = vkt_in_use / vkt_total * 100, # [%]
      
      time_stop = time_total - time_in_use, # [s]
      
      time_in_use.bike = time_in_use / num_bikes, # [s/bike]
      time_in_use.time = time_in_use / time_total * 100, # [%]
      
      time_stop.bike = time_stop / num_bikes, # [s/bike]
      time_stop.time = time_stop / time_total * 100, # [%]
    ) %>% 
    dplyr::add_row(total)
  
}

df <- pbapply::pblapply(path_dir, process) %>% 
  dplyr::bind_rows(.id = "run")

config_nom <- jsonlite::fromJSON("../data/config_mode_0.json")

variables <- colnames(df)
parameters <- variables[3:11]
parameters_labels <- c(
  "Mode", "Fleet size [-]", "Maximum walk radius [m]", "Average riding speed [km/h]", "Average walking speed [km/h]",
  "Rebalancing parameter [%]", "Min bikes/docks per station [-]", "Magic docks min [-]", "User trip file [-]")
metrics <- variables[12:length(variables)]
metrics_labels <- c(
  "Time total [s]", "Time total, per bike [s]", 
  "Time in use [s]", "VKT in use [km]",
  "Num users [-]", "Time walk origin average [s]", 
  "Time walk destination average [s]", "Time ride average [s]",
  "Time trip average [s]", 
  "Walk over 10 min at origin [-]",  "Walk over 15 min at origin [-]",  
  "Walk over 10 min at origin [%]", "Walk over 15 min at origin [%]",
  "Walk over 10 min at destination [-]",  "Walk over 15 min at destination [-]",  
  "Walk over 10 min at destination [%]", "Walk over 15 min at destination [%]",
  "Stations visited at origin [-]", "Stations visited at destination [-]",
  "Num trips [-]", "Trips served [-]", "Trips served [%]", 
  "Trips unserved no walkable stations [-]", "Trips unserved no bikes [-]", 
  "Trips unserved [-]",  "Trips unserved [%]", 
  "Num magic bikes [-]", "Num magic docks [-]", "Rebalanced bikes [-]",
  "Num days [-]", "Trips per bike and day [-]", 
  "Num used bikes [-]", "Num trips per bike in use and day [-]", 
  "Num bikes in use [-]", "Bikes in use [%]", 
  "Num bikes idle [-]", "Bikes idle [%]",
  "VKT total [km]", "VKT total, per bike [km]",
  "VKT in use, per bike [km]", "VKT in use, per dist [%]", 
  "Time idle [s]", "Time in use, per bike [s]", "Time in use, per time [%]", 
  "Time idle, per bike [s]", "Time idle, per time [%]"
)



parameters_idx <- seq(length(parameters))
metrics_idx <- seq(length(metrics))

parameters_idx <- setdiff(seq(length(parameters)), c(1,2,8,9))
metrics_idx <- setdiff(seq(length(metrics)), c(1,2,5,20,28))

metrics_idx <- c(35,29,18,19,31,22,26,3,44,8,42,46,9,6,7,23,24,4,38,39,40,41,12,13,16,17)

num_sim <- df$interval %>% is.na %>% sum
rows_per_sim <- df %>% dplyr::group_by(run) %>% dplyr::summarise(n=dplyr::n()) %>% dplyr::pull(n)

grid <- c(6,6,6,6,6,5)
effect <- rep(rep(c(3,4,5,6,7,9), grid), 10)
effect <- rep(effect, rows_per_sim)


# PLOT 1 ------------------------------------------------------------------


# for(i in parameters_idx){
#   for(j in metrics_idx){
i <- 4
j <- 6

p <- parameters[i]
m <- metrics[j]
plabel <- parameters_labels[i]
mlabel <- metrics_labels[j]

df %>% 
  dplyr::mutate(effect = effect) %>% 
  dplyr::filter(is.na(interval)) %>% 
  dplyr::filter(effect == i) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_point(ggplot2::aes(x=num_bikes, y=get(m), color=factor(get(p)) ) )+
  # ggplot2::geom_smooth(ggplot2::aes(x=num_bikes, y=get(m), color=factor(get(p)) ), 
  #                      method = 'loess', formula = 'y ~ x', level=0.6,
  #                      alpha=0.3, linetype=0 )+
  # ggplot2::geom_line(ggplot2::aes(x=num_bikes, y=get(m), color=factor(get(p)) ) )+
  ggplot2::scale_color_viridis_d()+
  ggplot2::labs(x="Fleet size", y=mlabel, color=plabel)+
  ggplot2::theme_bw()
# ggplot2::ggsave(paste0("figures/plot", "_x_", "num_bikes", "_z_", p, "_y_", m, ".png"), 
                # device = "png", width=12, height = 8)



# PLOT 2 ------------------------------------------------------------------


for(i in parameters_idx){
p <- parameters[i]
plabel <- parameters_labels[i]
print(i)
df %>% 
  dplyr::mutate(effect = effect) %>% 
  dplyr::filter(is.na(interval)) %>% 
  dplyr::filter(effect == i) %>% 
  data.table::setnames(metrics, metrics_labels) %>% 
  tidyr::pivot_longer(cols = metrics_labels[metrics_idx]) %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=num_bikes, y=value, color=factor(get(p)) ) )+
  ggplot2::geom_point(ggplot2::aes(x=num_bikes, y=value, color=factor(get(p)) ) )+
  ggplot2::scale_color_viridis_d(direction = -1)+
  ggplot2::facet_wrap(.~(name), ncol = 4, scales = "free_y")+
  ggplot2::labs(x="Fleet size", y=NULL, color=plabel)+
  ggplot2::theme_bw(base_family = "Ubuntu")+
  ggplot2::guides(color=ggplot2::guide_legend(nrow=1,byrow=TRUE))+
  ggplot2::theme(
    plot.margin = grid::unit(c(0, 0, 0, 0), "null"),
    # panel.spacing = grid::unit(c(0, 0, 0, 0), "null"),
    legend.title = ggplot2::element_text(size=10),
    legend.margin= ggplot2::margin(c(0,0,0,0)),
    legend.position = "bottom",
    strip.text = ggplot2::element_text(size=6),
    axis.text = ggplot2::element_text(size=6),
    axis.title.x = ggplot2::element_text(margin = ggplot2::margin(7,0,0,0))
  )+
  ggplot2::ggsave(paste0("figures/plot_SB", "_x_", "num_bikes", "_z_", p, ".pdf"), 
                  width=9, height = 11)
}


# PLOT 3 ------------------------------------------------------------------


for(i in parameters_idx){
p <- parameters[i]
plabel <- parameters_labels[i]

for(num_bikes_ in df$num_bikes %>% unique()){

df %>% 
  dplyr::mutate(effect = effect) %>% 
  dplyr::filter(!is.na(interval)) %>% 
  dplyr::filter(effect == i, num_bikes == num_bikes_) %>% 
  tidyr::pivot_longer(cols = metrics[metrics_idx]) %>%
  # dplyr::mutate(name = factor(name, labels = metrics_labels[metrics_idx][order(metrics[metrics_idx])])) %>%
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=interval, y=value, color=factor(get(p)), linetype=factor(num_bikes) ), alpha=0.8 )+
  ggplot2::scale_color_viridis_d(direction = -1)+
  ggplot2::facet_wrap(.~name, nrow = 6, ncol = 6, scales = "free_y")+
  ggplot2::labs(x="Time", y="Value", color=plabel, linetype="Num Bikes")+
  ggplot2::theme_bw()+
  ggplot2::theme(strip.text = ggplot2::element_text(size=8))+
  ggplot2::ggsave(paste0("figures/plot", "_x_", "time", "_z_", p, "_numbikes_", num_bikes_, ".png"), 
                  device = "png", width=16, height = 9, dpi=100)

}
}


# SEND CSV ----------------------------------------------------------------

df %>% 
  dplyr::filter(is.na(interval)) %>% 
  write.csv(file="stationbased_metrics_multiple.csv", row.names = F)

df %>% 
  dplyr::filter(num_bikes == 3500) %>% 
  dplyr::slice(1:169) %>% 
  write.csv(file="stationbased_metrics_single.csv", row.names = F)
