library(magrittr)

path <- "../results/2021-05-02_20-07-06/"
path <- "../results/2021-05-02_20-14-19/"
path <- "../results/2021-05-02_20-40-44/"
path <- "../results/2021-05-02_20-51-35/"

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




bike_trips %>% 
  dplyr::group_by(bike_id) %>% 
  dplyr::arrange(time_departure) %>% 
  dplyr::mutate(charging = !is.na(time_charge)) %>% 
  dplyr::ungroup() %>% 
  ggplot2::ggplot()+
  ggplot2::geom_line(ggplot2::aes(x=time_departure, y=battery_in, group=bike_id, color=charging), alpha=0.1)+
  ggplot2::scale_y_continuous(limits=c(0,100))+
  ggplot2::scale_color_manual(values = c("#393E41","#F0E100"))+
  ggplot2::ggtitle(paste0("Battery consumption", 
                          " | min level: ", config$BATTERY_MIN_LEVEL,
                          " | autonomy: ", config$BATTERY_AUTONOMY,
                          " | charge time: ", config$BATTERY_CHARGE_TIME))+
  ggplot2::ggsave(paste0("battery_consumption_", 
                         config$BATTERY_MIN_LEVEL, "_",
                         config$BATTERY_AUTONOMY, "_",
                         config$BATTERY_CHARGE_TIME, ".png"),
                         width=9, height=6
  )

num_bikes_use <- bike_trips$bike_id %>% unique %>% length
bike_trips %>% 
  dplyr::group_by(bike_id) %>% 
  dplyr::arrange(time_departure) %>% 
  dplyr::summarise(battery = dplyr::last(battery_in)) %>% 
  dplyr::ungroup() %>% 
  ggplot2::ggplot()+
  ggplot2::geom_histogram(ggplot2::aes(x=battery), binwidth=1)+
  ggplot2::geom_hline(ggplot2::aes(yintercept=num_bikes_use/100), linetype="dashed", color="blue")+
  ggplot2::scale_x_continuous(limits=c(0,100))+
  ggplot2::ggtitle(paste0("Battery distribution", 
                          " | min level: ", config$BATTERY_MIN_LEVEL,
                          " | autonomy: ", config$BATTERY_AUTONOMY,
                          " | charge time: ", config$BATTERY_CHARGE_TIME))+
  ggplot2::ggsave(paste0("battery_distribution_", 
                         config$BATTERY_MIN_LEVEL, "_",
                         config$BATTERY_AUTONOMY, "_",
                         config$BATTERY_CHARGE_TIME, ".png"),
                  width=9, height=6
  )

