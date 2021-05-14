library(magrittr)

path_experiments <- "../results/autonomous-20-04-2021"
path_dir <- list.files(path_experiments, full.names = T)
path <- path_dir[1]

process <- function(path){
  
  config <- jsonlite::fromJSON(file.path(path, "config.json"))
  user_trips <- data.table::fread(file.path(path, "user_trips.csv"), na.strings = "None")
  bike_trips <- data.table::fread(file.path(path, "bike_trips.csv"), na.strings = "None")
  
  
  df_config <- data.frame(
    mode = config$MODE, # []
    num_bikes = config$NUM_BIKES, # []
    autonomous_radius = config$AUTONOMOUS_RADIUS, # [m]
    riding_speed = config$RIDING_SPEED, # [km/h]
    autonomous_speed = config$AUTONOMOUS_SPEED, # [km/h]
    battery_min_level = config$BATTERY_MIN_LEVEL, # [%]
    battery_autonomy = config$BATTERY_AUTONOMY, # [km]
    battery_charge_time = config$BATTERY_CHARGE_TIME, # [h]
    user_trips_file = config$USER_TRIPS_FILE # [-]
  )
  
  
  # DATES -------------------------------------------------------------------
  
  origin <- "2019-10-07"
  freq_hour <- 60*60
  freq_day <- 24*60*60
  peak_times <- c(seq(7*60+50, 9*60+30), seq(15*60+50, 18*60+30))
  
  # ABSOLUTE VALUES ---------------------------------------------------------
  
  bike_stats <- bike_trips %>% 
    # CONFIG
    merge(df_config) %>% 
    dplyr::summarise(
      time_pickup = sum(ifelse(trip_type==1, time_ride, 0)), # [s]
      time_charging = sum(ifelse(trip_type==2, time_ride, 0)), # [s]
      time_rebalancing = sum(ifelse(trip_type==3, time_ride, 0)), # [s]
      
      vkt_pickup = time_pickup * config$AUTONOMOUS_SPEED / 3.6 / 1000, # [km]
      vkt_charging = time_charging * config$AUTONOMOUS_SPEED / 3.6 / 1000, # [km]
      vkt_rebalancing = time_rebalancing * config$AUTONOMOUS_SPEED / 3.6 / 1000, # [km]
      
      num_recharges = sum(trip_type==2),
      .groups = "keep"
    )
  
  
  
  user_trips %>% 
    # CONFIG
    merge(df_config) %>% 
    # TODO: remove 
    dplyr::mutate(
      time_trip = time_ride,
      time_ride = time_ride - time_wait) %>%
    dplyr::summarise(
      # CONFIG
      mode = mode, # []
      num_bikes = num_bikes, # []
      autonomous_radius = autonomous_radius, # [m]
      riding_speed = riding_speed, # [km/h]
      autonomous_speed = autonomous_speed, # [km/h]
      battery_min_level = battery_min_level, # [%]
      battery_autonomy = battery_autonomy, # [km]
      battery_charge_time = battery_charge_time, # [h]
      user_trips_file = user_trips_file, # [-]
      
      # VEHICLES
      time_total = diff(range(time_departure, na.rm=T))*num_bikes, # [s]
      time_total.bike = time_total / num_bikes, # [s/bike]
      
      time_in_use = sum(time_ride, na.rm=T), # [s]
      vkt_in_use = time_in_use * config$RIDING_SPEED / 3.6 / 1000, # [km]
      
      # USERS
      num_users = dplyr::n(), # []
      time_wait_avg = mean(time_wait, na.rm=T), # [s]
      time_ride_avg = mean(time_ride, na.rm=T), # [s]
      time_trip_avg = mean(time_wait + time_ride, na.rm=T), # [s]
      
      wait_over_10min = sum(time_wait > 10*60, na.rm=T), # []
      wait_over_15min = sum(time_wait > 15*60, na.rm=T), # []
      wait_over_10min.user = wait_over_10min/num_users * 100, # [%]
      wait_over_15min.user = wait_over_15min/num_users * 100, # [%]
      
      
      # TRIPS
      num_trips = dplyr::n(), # []
      served_trips = sum(!is.na(time_ride)), # []
      unserved_trips = num_trips - served_trips, # []
      # unserved_trips_no_bikes = sum(is.na(time_walk_origin)), # NO INFORMATION FOR THIS
      
      # EXTRA VEHICLES
      num_days = time_total.bike / (60 * 60 * 24), # [day]
      num_trips_bike_day = served_trips / num_bikes / num_days, # []
      
      num_used_bikes = length(unique(bike_id)),
      num_trips_bike_in_use_day = served_trips / num_used_bikes / num_days, # []
      
      .groups = "keep"
    ) %>% 
    dplyr::distinct() %>% 
    # BIKE TRIPS
    merge(bike_stats) %>% 
    dplyr::mutate(
      
      vkt_total = vkt_in_use + vkt_pickup + vkt_charging + vkt_rebalancing,
      vkt_total.bike = vkt_total / num_bikes,
      
      vkt_in_use.bike = vkt_in_use / num_bikes, # [km/bike]
      vkt_in_use.dist = vkt_in_use / vkt_total * 100, # [%]
      
      vkt_pickup.bike = vkt_pickup / num_bikes, # [km/bike]
      vkt_pickup.dist = vkt_pickup / vkt_total * 100, # [%]
      
      vkt_charging.bike = vkt_charging / num_bikes, # [km/bike]
      vkt_charging.dist = vkt_charging / vkt_total * 100, # [%]
      
      vkt_rebalancing.bike = vkt_rebalancing / num_bikes, # [km/bike]
      vkt_rebalancing.dist = vkt_rebalancing / vkt_total * 100, # [%]
      
      
      time_stop = time_total - time_in_use - time_pickup - time_charging - time_rebalancing, # [s]
      
      time_in_use.bike = time_in_use / num_bikes, # [s/bike]
      time_in_use.time = time_in_use / time_total * 100, # [%]
      
      time_pickup.bike = time_pickup / num_bikes, # [s/bike]
      time_pickup.time = time_pickup / time_total * 100, # [%]
      
      time_charging.bike = time_charging / num_bikes, # [s/bike]
      time_charging.time = time_charging / time_total * 100, # [%]
      
      time_rebalancing.bike = time_rebalancing / num_bikes, # [s/bike]
      time_rebalancing.time = time_rebalancing / time_total * 100, # [%]
      
      time_stop.bike = time_stop / num_bikes, # [s/bike]
      time_stop.time = time_stop / time_total * 100, # [%]
      
      
      num_recharges_day = num_recharges / num_days, # []
    ) %>% 
    tibble::rowid_to_column("interval") %>% 
    dplyr::mutate(interval = NA) -> total
  # t %>% as.data.frame %>% tibble::rownames_to_column() %>% `colnames<-`(c("variable", "value"))
  
  # return(total)
  # PER HOUR
  
  freq <- 60*60
  bikes_id <- seq(config$NUM_BIKES)-1
  
  bike_stats.hour <- bike_trips %>% 
    # CONFIG
    merge(df_config) %>% 
    dplyr::mutate(
      time = time_departure,
      interval = floor(time / freq),
    ) %>% 
    dplyr::group_by(interval) %>% 
    dplyr::summarise(
      time_pickup = sum(ifelse(trip_type==1, time_ride, 0)), # [s]
      time_charging = sum(ifelse(trip_type==2, time_ride, 0)), # [s]
      time_rebalancing = sum(ifelse(trip_type==3, time_ride, 0)), # [s]
      
      vkt_pickup = time_pickup * config$AUTONOMOUS_SPEED / 3.6 / 1000, # [km]
      vkt_charging = time_charging * config$AUTONOMOUS_SPEED / 3.6 / 1000, # [km]
      vkt_rebalancing = time_rebalancing * config$AUTONOMOUS_SPEED / 3.6 / 1000, # [km]
      
      num_recharges = sum(trip_type==2),
      
      .groups = "keep"
    )
  
  user_trips %>% 
    # CONFIG
    merge(df_config) %>% 
    # TODO: remove 
    dplyr::mutate(
      time_trip = time_ride,
      time_ride = time_ride - time_wait) %>%
    dplyr::mutate(
      time = time_departure,
      interval = floor(time / freq),
    ) %>% 
    dplyr::group_by(interval) %>% 
    dplyr::summarise(
      # CONFIG
      mode = mode, # []
      num_bikes = num_bikes, # []
      autonomous_radius = autonomous_radius, # [m]
      riding_speed = riding_speed, # [km/h]
      autonomous_speed = autonomous_speed, # [km/h]
      battery_min_level = battery_min_level, # [%]
      battery_autonomy = battery_autonomy, # [km]
      battery_charge_time = battery_charge_time, # [h]
      user_trips_file = user_trips_file, # [-]
      
      # VEHICLES
      time_total = diff(range(time_departure, na.rm=T))*num_bikes, # [s]
      time_total.bike = time_total / num_bikes, # [s/bike]
      
      time_in_use = sum(time_ride, na.rm=T), # [s]
      vkt_in_use = time_in_use * config$RIDING_SPEED / 3.6 / 1000, # [km]
      
      # USERS
      num_users = dplyr::n(), # []
      time_wait_avg = mean(time_wait, na.rm=T), # [s]
      time_ride_avg = mean(time_ride, na.rm=T), # [s]
      time_trip_avg = mean(time_wait + time_ride, na.rm=T), # [s]
      
      wait_over_10min = sum(time_wait > 10*60, na.rm=T), # []
      wait_over_15min = sum(time_wait > 15*60, na.rm=T), # []
      wait_over_10min.user = wait_over_10min/num_users * 100, # [%]
      wait_over_15min.user = wait_over_15min/num_users * 100, # [%]
      
      
      # TRIPS
      num_trips = dplyr::n(), # []
      served_trips = sum(!is.na(time_ride)), # []
      unserved_trips = num_trips - served_trips, # []
      # unserved_trips_no_bikes = sum(is.na(time_walk_origin)), # NO INFORMATION FOR THIS
      
      # EXTRA VEHICLES
      num_days = time_total.bike / (60 * 60 * 24), # [day]
      num_trips_bike_day = served_trips / num_bikes / num_days, # []
      
      num_used_bikes = length(unique(bike_id)),
      num_trips_bike_in_use_day = served_trips / num_used_bikes / num_days, # []
      
      .groups = "keep"
    ) %>% 
    dplyr::distinct() %>% 
    # BIKE TRIPS
    merge(bike_stats.hour) %>% 
    dplyr::mutate(
      
      vkt_total = vkt_in_use + vkt_pickup + vkt_charging + vkt_rebalancing,
      vkt_total.bike = vkt_total / num_bikes,
      
      vkt_in_use.bike = vkt_in_use / num_bikes, # [km/bike]
      vkt_in_use.dist = vkt_in_use / vkt_total * 100, # [%]
      
      vkt_pickup.bike = vkt_pickup / num_bikes, # [km/bike]
      vkt_pickup.dist = vkt_pickup / vkt_total * 100, # [%]
      
      vkt_charging.bike = vkt_charging / num_bikes, # [km/bike]
      vkt_charging.dist = vkt_charging / vkt_total * 100, # [%]
      
      vkt_rebalancing.bike = vkt_rebalancing / num_bikes, # [km/bike]
      vkt_rebalancing.dist = vkt_rebalancing / vkt_total * 100, # [%]
      
      
      time_stop = time_total - time_in_use - time_pickup - time_charging - time_rebalancing, # [s]
      
      time_in_use.bike = time_in_use / num_bikes, # [s/bike]
      time_in_use.time = time_in_use / time_total * 100, # [%]
      
      time_pickup.bike = time_pickup / num_bikes, # [s/bike]
      time_pickup.time = time_pickup / time_total * 100, # [%]
      
      time_charging.bike = time_charging / num_bikes, # [s/bike]
      time_charging.time = time_charging / time_total * 100, # [%]
      
      time_rebalancing.bike = time_rebalancing / num_bikes, # [s/bike]
      time_rebalancing.time = time_rebalancing / time_total * 100, # [%]
      
      time_stop.bike = time_stop / num_bikes, # [s/bike]
      time_stop.time = time_stop / time_total * 100, # [%]
      
      
      num_recharges_day = num_recharges / num_days, # []
    ) %>% 
    dplyr::add_row(total)
  
}

path <- "../results/2021-04-20_23-35-47/"

df <- pbapply::pblapply(path_dir, process) %>% 
  dplyr::bind_rows(.id = "run")

config_nom <- jsonlite::fromJSON("../data/config_mode_2.json")

variables <- colnames(df)
parameters <- variables[3:11]
parameters_labels <- c(
  "Mode", "Fleet size [-]", "Autonomous radius [m]", "Riding speed [km/h]", "Autonomous speed [km/h]",
  "Battery min level [%]", "Battery autonomy [km]", "Battery charge time [h]", "User trip file [-]")
metrics <- variables[12:length(variables)]
metrics_labels <- c(
  "Time total [s]", "Time total, per bike [s]", "Time in use [s]", "VKT in use [km]",
  "Num users [-]", "Time wait average [s]", "Time ride average [s]", "Time trip average [s]",
  "Wait over 10 min [-]", "Wait over 15 min [-]", "Wait over 10 min, per user [%]", "Wait over 15 min, per user [%]",
  "Num trips [-]", "Served trips [-]", "Unserved trips [-]", "Num days [-]",
  "Num trips per bike and day [-]", "Num used bikes [-]", "Num trips per bike in use and day [-]", "Time pickup [s]",
  "Time charging [s]", "Time rebalancing [s]", "VKT pickup [km]", "VKT charging [km]",
  "VKT rebalancing [km]", "Num recharges [-]", "VKT total [km]", "VKT total, per bike [km]",
  "VKT in use, per bike [km]", "VKT in use, per dist [%]", "VKT pickup, per bike  [km]", "VKT pickup, per dist [%]",
  "VKT charging, per bike [km]", "VKT charging, per dist [%]", "VKT rebalancing, per bike [km]", "VKT rebalancing, per dist [%]",
  "Time stop [s]", "Time in use, per bike [s]", "Time in use, per time [%]", "Time pickup, per bike [s]",
  "Time pickup, per time [%]", "Time charging, per bike [s]", "Time charging, per time [%]", "Time rebalancing, per bike [s]",
  "Time rebalancing, per time [%]", "Time stop, per bike [s]", "Time stop, per time [%]", "Num recharges, per day [-]"
)




parameters_idx <- seq(length(parameters))
metrics_idx <- seq(length(metrics))

parameters_idx <- setdiff(seq(length(parameters)), c(1,2,9))
metrics_idx <- setdiff(seq(length(metrics)), c(1,2,5,13,16,48))
# metrics_idx <- c(6,7,8,9,10,14)

num_sim <- df$interval %>% is.na %>% sum
rows_per_sim <- df %>% dplyr::group_by(run) %>% dplyr::summarise(n=dplyr::n()) %>% dplyr::pull(n)


grid <- c(6,6,6,6,6,6,5)
effect <- rep(rep(seq(3,9), grid), 10)
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

df %>% 
  dplyr::mutate(effect = effect) %>% 
  dplyr::filter(is.na(interval)) %>% 
  dplyr::filter(effect == i) %>% 
  tidyr::pivot_longer(cols = metrics[metrics_idx]) %>%
  dplyr::mutate(name = factor(name, labels = metrics_labels[metrics_idx][order(metrics[metrics_idx])])) %>%
  ggplot2::ggplot()+
  ggplot2::geom_point(ggplot2::aes(x=num_bikes, y=value, color=factor(get(p)) ) )+
  ggplot2::scale_color_viridis_d(direction = -1)+
  ggplot2::facet_wrap(.~name, nrow = 6, ncol = 7, scales = "free_y")+
  ggplot2::labs(x="Fleet size", y="Value", color=plabel)+
  ggplot2::theme_bw()+
  ggplot2::theme(strip.text = ggplot2::element_text(size=6),
                 legend.position = "right")+
  ggplot2::ggsave(paste0("figures/plot", "_x_", "num_bikes", "_z_", p, ".png"), 
                  device = "png", width=16, height = 9, dpi=200)
}


# PLOT 3 ------------------------------------------------------------------


df %>% dplyr::filter(!is.na(interval), num_bikes==3000, autonomous_radius==2000) %>% 
  dplyr::select(interval, time_ride_avg) %>% plot(t="l")

for(i in parameters_idx){
p <- parameters[i]
plabel <- parameters_labels[i]

for(num_bikes in df$num_bikes %>% unique()){
  
df %>% 
  dplyr::mutate(effect = effect) %>% 
  dplyr::filter(!is.na(interval)) %>% 
  dplyr::filter(effect == i, num_bikes == num_bikes) %>% 
  tidyr::pivot_longer(cols = metrics[metrics_idx]) %>%
  # dplyr::mutate(name = factor(name, labels = metrics_labels[metrics_idx][order(metrics[metrics_idx])])) %>%
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=interval, y=value, color=factor(get(p)) ), alpha=0.8 )+
  ggplot2::scale_color_viridis_d(direction = -1)+
  ggplot2::facet_wrap(.~name, nrow = 6, ncol = 7, scales = "free_y")+
  ggplot2::labs(x="Time", y="Value", color=plabel)+
  ggplot2::theme_bw()+
  ggplot2::theme(strip.text = ggplot2::element_text(size=8))
  ggplot2::ggsave(paste0("figures/plot", "_x_", "time", "_z_", p, ".png"), 
                  device = "png", width=16, height = 9, dpi=200)

}
}
# SEND CSV ----------------------------------------------------------------

df %>% 
  dplyr::filter(is.na(interval)) %>% View
write.csv(file="autonomous_metrics_multiple.csv", row.names = F)

df %>% 
  dplyr::filter(num_bikes == 800) %>% 
  dplyr::slice(1:169) %>% 
  write.csv(file="autonomous_metrics_single.csv", row.names = F)
