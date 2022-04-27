library(magrittr)


# DEMAND TRAINING DATA ----------------------------------------------------
trip_files <- list.files('bluebikes_data', pattern = "*.zip", full.names = T)

grid <- 750 # [m]
lat_center <- 42.35
lat_size <- grid / 111320
lon_size <- grid / (40075000 * cos(lat_center * pi / 180) / 360)
freq <- 15*60

df_training <- lapply(trip_files, function(f){
  print(f)
  data.table::fread(cmd = paste0("unzip -p ", f)) %>% 
    dplyr::rename_all(stringr::str_replace_all, " ", "_") %>% 
    dplyr::rename_all(tolower) %>% 
    dplyr::mutate(
      startdate = lubridate::as_datetime(starttime, tz = "US/Eastern"),
      startunix = as.integer(as.numeric(startdate))
    ) %>% 
    dplyr::select(time=startunix, lon=start_station_longitude, lat=start_station_latitude) %>%
    dplyr::mutate(
      group_time = freq * floor(time / freq),
      group_lon = lon_size * floor(lon / lon_size),
      group_lat = lat_size * floor(lat / lat_size)
    ) %>%
    dplyr::group_by(group_time, group_lon, group_lat) %>% 
    dplyr::summarise(count = dplyr::n()) %>% 
    dplyr::ungroup() %>% 
    dplyr::select(time=group_time, lon=group_lon, lat=group_lat, count) %>% 
    tidyr::complete(time, tidyr::nesting(lon, lat), fill = list(count = 0), explicit=F)
}) %>% dplyr::bind_rows() %>% 
  dplyr::group_by(lon, lat) %>%
  dplyr::mutate(cell = dplyr::cur_group_id()) %>%
  dplyr::ungroup() %>% 
  tidyr::complete(time, tidyr::nesting(cell, lon, lat), fill = list(count = 0), explicit=F) %>% 
  write.csv("training_data.csv", row.names = F)
