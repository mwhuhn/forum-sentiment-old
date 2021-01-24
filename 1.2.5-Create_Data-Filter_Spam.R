# 1.2.5 Identify Spam

# Libraries ----

library(tidyverse)
library(randomForest)
library(rsample)

# Path ----

path_parent <- dirname(dirname(rstudioapi::getSourceEditorContext()$path))

# Load files ----

samp <- read.csv(paste0(path_parent, "/clean_data/spam_sample.txt"), sep = "\t")

# Add subsample and fill down ----

make_bool <- function(x) {
  return(x=="True")
}

coded <- samp %>%
  filter(!is.na(spam))

test <- coded %>%
  mutate(
    spam = replace_na(spam, 0),
    is_spam = factor(ifelse(spam==1, "yes", "no"), levels = c("no", "yes")),
    n_char = nchar(text),
    is_long = n_char > 900,
    many_symbols = n_symbols > 10
  ) %>%
  select(
    # is_spam, many_symbols, is_long, has_url, has_email, has_large_number, enlargement, supplement, streaming, stream, live, vs, watch, vashikaran
    is_spam, many_symbols, is_long, has_url, has_email, has_large_number, enlargement, black.magic, male.enhancement, s3xual, love.spell, astrologer, supplement, aminoapp, xtreme, extreme, keto, streaming, stream, live, vs, watch, vashikaran, visit.us.at
  ) %>%
  mutate(across(has_url:vashikaran, make_bool))

# Create train and validation set

set.seed(2352)
train_test_split <- initial_split(test, prop = 0.9)
spam_train <- training(train_test_split)
spam_test <- testing(train_test_split)
# validation_data <- mc_cv(spam_train, prop = 0.9, times = 30)
# validation_data

# Train model

model_logit <- glm(is_spam ~ ., data = spam_train, family = "binomial")
summary(model_logit)
pred_p.logit <- predict(model_logit, spam_train, type = "response")
pred.logit <- ifelse(spam_train$pred_p > .5, 1, 0)
table(pred=pred.logit, true=spam_train$is_spam)

model_rf <- randomForest(is_spam ~ ., data = spam_train, importance = TRUE)
model_rf
pred.rf <- predict(model_rf, spam_train, type = "response")
table(pred=pred.rf, true=spam_train$is_spam)



model2 <- randomForest(Condition ~ ., data = TrainSet, ntree = 500, mtry = 6, importance = TRUE)