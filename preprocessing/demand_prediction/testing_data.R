library(magrittr)


# DEMAND TESTING DATA ----------------------------------------------------

date_lb <- "2019-10-07 00:00:00"
unix_lb <- lubridate::as_datetime(date_lb, tz = "US/Eastern") %>% as.numeric
date_ub <- "2019-10-14 00:00:00"
unix_ub <- lubridate::as_datetime(date_ub, tz = "US/Eastern") %>% as.numeric

grid <- 750 # [m]
lat_center <- 42.35
lat_size <- grid / 111320
lon_size <- grid / (40075000 * cos(lat_center * pi / 180) / 360)
freq <- 15*60

data.table::fread("testing_data.csv") %>% 
  dplyr::rename_all(stringr::str_replace_all, " ", "_") %>% 
  dplyr::rename_all(tolower) %>% 
  dplyr::mutate(
    ts = lubridate::as_datetime(timebin, tz = "US/Eastern"),
    unix = as.numeric(ts),
  ) %>% 
  dplyr::filter(dplyr::between(unix, unix_lb, unix_ub)) %>% 
  tidyr::uncount(count_pred) %>% 
  dplyr::mutate(
    group_lon = floor(lon / lon_size),
    group_lat = floor(lat / lat_size),
    lon_lb = round(group_lon * lon_size, 5),
    lon_ub = round(lon_lb + lon_size, 5),
    lat_lb = round(group_lat * lat_size, 5),
    lat_ub = round(lat_lb + lat_size, 5),
    group_lon = group_lon - min(group_lon),
    group_lat = group_lat - min(group_lat),
  ) %>% 
  dplyr::select(ts, unix, lon, lat, group_lon, group_lat, lon_lb, lon_ub, lat_lb, lat_ub) %>% 
  dplyr::mutate(ts = unix - min(unix)) %>% 
  dplyr::arrange(ts) %>% 
  write.csv("demand_grid.csv", row.names = F)
