# 2.1 Sentiment-Seasonality

# Libraries ----

library(tidyverse)
library(forecast)
library(lubridate)

# Path ----

path_parent <- dirname(dirname(rstudioapi::getSourceEditorContext()$path))

# Load files ----

sn <- read.csv(paste0(path_parent,"/clean_data/sn_sentiment.csv"))
td <- read.csv(paste0(path_parent,"/clean_data/td_sentiment.csv"))

# Clean data ----

days <- c("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday")
months <- c("January","February","March","April","May","June",
            "July","August","September","October","November","December")
periods <- c("before","march","during")

pad <- function(n) {
  if(is.character(n)) {
    t <- as.numeric(n)
  } else {
    t <- n
  }
  if(t < 10) {
    return(paste0("0", as.character(t)))
  } else {
    return(as.character(t))
  }
}

clean_data <- function(df) {
  df <- df %>%
    mutate(
      before = before == "True",
      march = march == "True",
      during = during == "True",
      period = factor(period, levels=periods),
      month = factor(month, levels=months),
      weekday = factor(weekday, levels=days),
      date_created = ymd_hms(date_created, tz="EST"),
      is_parent = is.na(parent_id),
      year = year(date_created)
    ) %>%
  filter(
    date_created < ymd(20201201) & date_created >= ymd(20140101)
  )
  return(df)
}

sn <- clean_data(sn)
td <- clean_data(td)

# Plot by year-week ----

## . scale x ----
weeks <- map_chr(c(1,14,27,40), pad)
years <- seq(2014,2020,1)
wy_scale <- apply(expand.grid(y=years, w=weeks), 1, paste, collapse="-")


## . plot frequency  ----

plot_freq <- function(df) {
  df %>%
    group_by(week_n, year) %>%
    summarise(
      freq = n(),
      .groups = 'drop_last'
    ) %>%
    mutate(
      week_n = map_chr(week_n, pad),
      wy = paste(year, week_n, sep="-")
    ) %>%
    ggplot(aes(x=wy, y=freq)) +
    geom_point() +
    scale_x_discrete(breaks=wy_scale, labels = wy_scale) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5))
}

plot_freq(sn)
plot_freq(td)

## . plot ave sentiment ----

plot_sen <- function(df) {
  df %>%
    group_by(week_n, year) %>%
    summarise(
      ave_sen = mean(com_sen_no_url),
      .groups = 'drop_last'
    ) %>%
    mutate(
      week_n = map_chr(week_n, pad),
      wy = paste(year, week_n, sep="-")
    ) %>%
    ggplot(aes(x=wy, y=ave_sen)) +
    geom_point() +
    scale_x_discrete(breaks=wy_scale, labels = wy_scale) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5))
}

plot_sen(sn)
plot_sen(td)

# 
