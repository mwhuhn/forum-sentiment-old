# 1.2.5 Identify Spam

# Libraries ----

library(tidyverse)
library(randomForest)
library(rsample)

# Path ----

path_parent <- dirname(dirname(rstudioapi::getSourceEditorContext()$path))

# Load files ----

samp <- read.csv(paste0(path_parent, "/clean_data/spam_sample.txt"), sep = "\t")

# Add sub-sample and fill down ----

make_bool <- function(x) {
  return(x=="True")
}

coded <- samp %>%
  filter(!is.na(spam)) %>%
  select(
    spam, message_id, text, text_clean, n_symbols, has_url, has_email, has_large_number, vashikaran:pills, enlarge:penis, male.enhancement:penis.size, supplement, astrologer, testosterone, visit.us.at, keto:visit.here
  ) %>%
  mutate(
    # spam = replace_na(spam, 0),
    is_spam = factor(ifelse(spam==1, "yes", "no"), levels = c("no", "yes")),
    n_char = nchar(text),
    is_long = n_char > 900,
    many_symbols = n_symbols > 10, 
    problem.solution = grepl("problem solution", text, ignore.case = T),
    amino.app = grepl("aminoapp", text, ignore.case = T),
    cbd.oil = grepl("cbd.oil", text, ignore.case = T),
    has_dd = grepl("\\bdd['s]*\\b", text_clean, ignore.case = T),
    has_dh = grepl("\\bdh['s]*\\b", text_clean, ignore.case = T),
    has_ds = grepl("\\bds['s]*\\b", text_clean, ignore.case = T)
  ) %>%
  mutate(across(has_url:visit.here, make_bool))

noncoded <- samp %>%
  filter(is.na(spam)) %>%
  select(
    spam, message_id, text, text_clean, n_symbols, has_url, has_email, has_large_number, vashikaran:pills, enlarge:penis, male.enhancement:penis.size, supplement, astrologer, testosterone, visit.us.at, keto:visit.here
  ) %>%
  mutate(
    # spam = replace_na(spam, 0),
    is_spam = factor(ifelse(spam==1, "yes", "no"), levels = c("no", "yes")),
    n_char = nchar(text),
    is_long = n_char > 900,
    many_symbols = n_symbols > 10, 
    problem.solution = grepl("problem solution", text, ignore.case = T),
    amino.app = grepl("aminoapp", text, ignore.case = T),
    cbd.oil = grepl("cbd.oil", text, ignore.case = T),
    has_dd = grepl("\\bdd['s]*\\b", text_clean, ignore.case = T),
    has_dh = grepl("\\bdh['s]*\\b", text_clean, ignore.case = T),
    has_ds = grepl("\\bds['s]*\\b", text_clean, ignore.case = T)
  ) %>%
  mutate(across(has_url:visit.here, make_bool))

  # ) %>%
  # select(
  #   # is_spam, many_symbols, is_long, has_url, has_email, has_large_number, enlargement, supplement, streaming, stream, live, vs, watch, vashikaran
  #   is_spam, many_symbols, is_long, has_url, has_email, has_large_number, enlargement, black.magic, male.enhancement, s3xual, love.spell, astrologer, supplement, aminoapp, xtreme, extreme, keto, streaming, stream, live, vs, watch, vashikaran, visit.us.at
  # ) %>%
  # mutate(across(has_url:vashikaran, make_bool))


# Explore ----

## . No Urls ----

table(spam=coded$spam, email=coded$has_url)
mask <- (!coded$has_url)
nonurls <- coded[mask,]
nonurls$problem.solution <- grepl("problem solution", nonurls$text, ignore.case = T)

## Always spam
# !has_url & vashikaran
# !has_url & has_large_number & n_char >= 900
# !has_url & has_large_number & n_symbols >= 10
# !has_url & has_large_number & problem.solution


## . Has Urls ----

urls <- coded[!mask,]
urls <- urls %>%

## Never spam
# has_dd
# has_dh
# has_ds

## Always spam (if not in never spam)
# has_url & vs & stream
# has_url & s.t.r.e.a.
# has_url & has_large_number
# has_url & visit.her
# has_url & amino.ap
# has_url & male_enhancement
# has_url & testosterone
# has_url & visit.us.at
# has_url & cbd.oil
# has_url & live & stream

## TODO: Code examples, will probably need topic modelling
# has_url & is_long
# has_url & watch & live & !stream # sports streams vs others
# has_url & keto # long ones are spam
# has_url & supplement # topic models
# has_url & pills



# Code spam ----
test <- noncoded %>%
  mutate(
    probable_spam = (!has_url & vashikaran) |
      (!has_url & has_large_number & is_long) |
      (!has_url & has_large_number & many_symbols) |
      (!has_url & has_large_number & problem.solution) | 
      (has_url & vs & stream) |
      (has_url & s.t.r.e.a.m) |
      (has_url & has_large_number) |
      (has_url & visit.here) |
      (has_url & amino.app) |
      (has_url & male.enhancement) |
      (has_url & testosterone) |
      (has_url & visit.us.at) |
      (has_url & cbd.oil)
  )
table(test$probable_spam)

test <- test %>%
  mutate(
    has_bracket_url = grepl("\\[url", text_clean, ignore.case = T),
    has_Http = grepl("Http", text_clean, ignore.case = F)
  )

table(t=test, spam=noncoded$spam)


# Create train and validation set ----

# validation_data <- mc_cv(spam_train, prop = 0.9, times = 30)
# validation_data

# Train model

# model_logit <- glm(is_spam ~ ., data = spam_train, family = "binomial")
# summary(model_logit)
# pred_p.logit <- predict(model_logit, spam_train, type = "response")
# pred.logit <- ifelse(spam_train$pred_p > .5, 1, 0)
# table(pred=pred.logit, true=spam_train$is_spam)


rf_no_url <- coded %>%
  filter(!has_url) %>%
  select(is_spam, vashikaran, creme, has_large_number, many_symbols, is_long, problem.solution)

set.seed(2352)
train_test_split <- initial_split(rf_no_url, prop = 0.9)
spam_train <- training(train_test_split)
spam_test <- testing(train_test_split)

model_rf <- randomForest(is_spam ~ ., data = spam_train, ntree = 10000, mtry = 3,importance = TRUE, keep.forest = TRUE)
model_rf
pred.rf <- predict(model_rf, spam_test, type = "response")
table(pred=pred.rf, true=spam_test$is_spam)




model2 <- randomForest(Condition ~ ., data = TrainSet, ntree = 4000, mtry = 3, importance = TRUE)
