# 3.1.5 Tune Topic Models

# Libraries ----

library(tidyverse)

library(gganimate)
library(png)
library(gifski)

# Path ----

path_parent <- dirname(dirname(rstudioapi::getSourceEditorContext()$path))

# Load files ----

sn_tune <- read.csv(paste0(path_parent,"/clean_data/a_b_t_tune_special-needs_parent_grid.csv"), header = F)
names(sn_tune) <- c("coherence", "perplexity", "n_topics", "alpha", "beta", "topic_n", "words")

# Explore models ----

sn_tune %>%
  filter(topic_n==0) %>%
  slice_max(coherence, n=10) %>%
  select(coherence:beta)

sn_tune %>%
  filter(topic_n==0) %>%
  ggplot(aes(x=n_topics, y=coherence)) +
  geom_point()

p <- sn_tune %>%
  filter(topic_n==0) %>%
  ggplot(aes(x=alpha, y=beta, color=coherence)) +
  geom_point(size=3, shape=15) +
  scale_color_distiller(palette = "Spectral") +
  theme_classic()

path_gif <- paste0(path_parent, "/plots/coherence_tuning.gif")

an <- p +
  transition_states(states = n_topics,
                    transition_length = 1,
                    state_length = 3) +
  labs(title="Topics: {closest_state}")

anim_save(path_gif, an, renderer=gifski_renderer(), duration=40, fps=10, width=5, height=4, units="in", res=100)


ggsave(paste0(path_parent, "/plots/coherence_tuning_,",n,"_topics.png"), width=5, height=4)

