rm(list=ls())

setwd("C:/Users/jshym/OneDrive/Documents/School/TU/Graduate/Research/Not All Explanatations Are Created Equal/chess_puzzle_explainer/instance")

library(RSQLite)
library(dplyr)
library(jsonlite)
library(ggplot2)
library(effectsize)

get_table_dfs <- function(db_filepath) {
  con <- dbConnect(drv=RSQLite::SQLite(), dbname=db_filepath)
  tables <- dbListTables(con)
  tables <- tables[tables != "sqlite_sequence"] # exclude sqlite_sequence (contains table information)
  t_dfs <- vector("list", length=length(tables))
  names(t_dfs) <- tables
  for (i in seq(along=tables)) {
    t_dfs[[i]] <- dbGetQuery(conn=con, statement=paste("SELECT * FROM '", tables[[i]], "'", sep=""))
  }
  dbDisconnect(con)
  return(t_dfs)
}

get_survey_dfs <- function(raw_surveys) {
  types <- unique(raw_surveys$type)
  s_dfs <- vector("list", length=length(types))
  names(s_dfs) <- types
  for (i in seq(along=types)) {
    old_survey_df <- raw_surveys[raw_surveys$type == types[[i]], ]
    new_survey_df <- old_survey_df %>% 
      rowwise() %>%
      do(data.frame(fromJSON(.$data, flatten = T))) %>%
      ungroup() %>%
      bind_cols(old_survey_df %>% select(-c(data,type)))
    s_dfs[[i]] <- new_survey_df
  }
  return(s_dfs)
}

start_date = as.POSIXct("2023-09-25")
restart_date = as.POSIXct("2023-10-01")

#### Obtain and clean SQLite table data frames ####

table_dfs <- get_table_dfs("application.db")

explanations <- table_dfs$explanation
explanations$protocol <- explanations$protocol %>% ordered(levels=c("none", "placebic", "actionable"))

moves <- table_dfs$move %>% filter(start_time > restart_date, mturk_id %>% startsWith("A"))
moves$start_time <- moves$start_time %>% as.POSIXct()
moves$end_time <- moves$end_time %>% as.POSIXct()
moves$mistake <- moves$mistake %>% as.logical()

puzzles <- table_dfs$puzzle
puzzles$theme <- puzzles$theme %>% as.factor()

sections <- table_dfs$section %>% filter(start_time > restart_date, mturk_id %>% startsWith("A"))
sections$section <- sections$section %>% as.factor()
sections$protocol <- sections$protocol %>% ordered(levels=c("none", "placebic", "actionable"))
sections$start_time <- sections$start_time %>% as.POSIXct()
sections$end_time <- sections$end_time %>% as.POSIXct()

surveys <- table_dfs$survey %>% filter(timestamp > restart_date, mturk_id %>% startsWith("A"))
surveys$timestamp <- surveys$timestamp %>% as.POSIXct()

users <- table_dfs$user %>% filter(start_time > restart_date, mturk_id %>% startsWith("A"))
users$experiment_completed <- users$experiment_completed %>% as.logical()
users$failed_attention_checks <- users$failed_attention_checks %>% as.logical()
users$start_time <- users$start_time %>% as.POSIXct()
users$end_time <- users$end_time %>% as.POSIXct()
users$consent <- users$consent %>% as.logical()
users$protocol <- users$protocol %>% ordered(levels=c("none", "placebic", "actionable"))
users$study_duration <- users$end_time - users$start_time
users$bonus_comp <- pmax(users$compensation - 2.5, 0)

#### Obtain and clean survey data frames ####

survey_dfs <- get_survey_dfs(surveys)

demographics <- survey_dfs$demographics
demographics$age <- demographics$age %>% as.ordered()
demographics$gender <- demographics$gender %>% as.factor()
demographics$ethnicity <- demographics$ethnicity %>% as.factor()
demographics$attention.check <- demographics$attention.check %>% as.integer()
demographics$chess.skill <- demographics$chess.skill %>% ordered(levels=c("Beginner", "Intermediate", "Expert"))

final_surveys <- survey_dfs$final_survey
final_surveys$sat.outcome.1 <- final_surveys$sat.outcome.1 %>% as.integer()
final_surveys$sat.outcome.2 <- final_surveys$sat.outcome.2 %>% as.integer()
final_surveys$sat.outcome.3 <- final_surveys$sat.outcome.3 %>% as.integer()
final_surveys$sat.agent.1 <- final_surveys$sat.agent.1 %>% as.integer()
final_surveys$sat.agent.2 <- final_surveys$sat.agent.2 %>% as.integer()
final_surveys$sat.agent.3 <- final_surveys$sat.agent.3 %>% as.integer()
final_surveys$exp.power.1 <- final_surveys$exp.power.1 %>% as.integer()
final_surveys$exp.power.2 <- final_surveys$exp.power.2 %>% as.integer()
final_surveys$exp.power.3 <- final_surveys$exp.power.3 %>% as.integer()
final_surveys$attention.check.1 <- final_surveys$attention.check.1 %>% as.integer()
final_surveys$attention.check.2 <- final_surveys$attention.check.2 %>% as.integer()

feedback <- survey_dfs$feedback
names(feedback)[1] <- "text"

#### Dropped Users ####

dropped_ids <- users %>% filter(experiment_completed == F) %>% select(mturk_id) %>% unlist()
users %>% filter(mturk_id %in% c(dropped_ids))
demographics %>% filter(mturk_id %in% dropped_ids)
sections %>% filter(mturk_id %in% dropped_ids, section == "practice")
sections %>% filter(mturk_id %in% dropped_ids, section == "testing")
final_surveys %>% filter(mturk_id %in% dropped_ids) %>% select(mturk_id)

#### Duration ####

users$study_duration %>% as.double() %>% median(na.rm = T)
(users %>% inner_join(demographics, join_by(mturk_id)) %>% mutate(login.demo.duration = timestamp - start_time) %>% select(login.demo.duration) %>% unlist()/60) %>% median(na.rm = T)
(demographics %>% inner_join(sections, join_by(mturk_id)) %>% filter(section == "practice") %>% mutate(add.info = start_time - timestamp) %>% select(add.info) %>% unlist()/60) %>% as.double() %>% median(na.rm = T)
(sections %>% filter(section == "practice") %>% select(duration) %>% unlist()/60000) %>% median(na.rm = T)
(sections %>% filter(section == "testing") %>% select(duration) %>% unlist()/60000) %>% median(na.rm = T)
(sections %>% inner_join(final_surveys, join_by(mturk_id)) %>% mutate(final_survey.duration = timestamp - end_time) %>% select(final_survey.duration) %>% unlist()/60) %>% median(na.rm = T)

#### Bonus Compensation ####

users %>% 
  select(mturk_id, completion_code, bonus_comp) %>% 
  filter(bonus_comp > 0) %>%
  arrange(mturk_id)

#### Protocols ####

users %>% select(protocol) %>% table()
users %>% filter(experiment_completed) %>% select(protocol) %>% table()

#### Demographics ####

demographics$chess.skill %>% table()

sections %>% 
  filter(section == "testing") %>% 
  inner_join(demographics, join_by(mturk_id)) %>% 
  ggplot(aes(x = chess.skill, y = successes)) + 
  geom_boxplot() + 
  ylab("successes")

#### Feedback ####

feedback %>% select(text, mturk_id) %>% print(n = 200)

#### Performance: Number of Moves ####

# Correlation between practice and testing
# Progression during practice or testing
# T-tests
# Bonus per puzzle
# Scale within puzzle
# New metric: Ask for theme after each puzzle
# New metric: Ask which pieces a move attacks
# Cloud Research
# Don't mix questions, color code factors

# Data wrangling
puzzle_stats <- moves %>% 
  inner_join(users, join_by(mturk_id)) %>% 
  group_by(mturk_id, section_id, puzzle_id, protocol) %>% 
  summarize(num_moves = n(), num_seconds = sum(duration)/1000, num_correct = sum(!mistake), score = 1/(num_moves*num_seconds)) %>% 
  inner_join(sections, join_by(mturk_id, section_id == id), suffix = c(".move", ".section")) %>% 
  rename(protocol.user = protocol.move) %>% 
  filter(section == "testing") %>% 
  ungroup()
# Data filtering
puzzle_stats %>% select(num_moves) %>% unlist() %>% hist() # Highly skewed data, not great for ANOVA testing
max_moves <- 12 # Limit "outliers" / tail end of distribution
puzzle_stats.few_moves <- puzzle_stats %>% filter(num_moves <= max_moves)
puzzle_stats.few_moves %>% select(num_moves) %>% unlist() %>% hist() # Improved distribution
nrow(puzzle_stats.few_moves) / nrow(puzzle_stats) # Proportion of original data
# Box plots
puzzle_stats %>% ggplot(aes(x = protocol.user, y = num_moves)) + geom_boxplot()
puzzle_stats.few_moves %>% ggplot(aes(x = protocol.user, y = num_moves)) + geom_boxplot() # Cut out most outliers
# Tests
anova.num_moves.all <- aov(num_moves ~ protocol.user, data = puzzle_stats)
anova.num_moves.few <- aov(num_moves ~ protocol.user, data = puzzle_stats.few_moves)
tukey.num_moves.all <- TukeyHSD(anova.num_moves.all)
tukey.num_moves.few <- TukeyHSD(anova.num_moves.few)
# Stats
anova.num_moves.all %>% summary()
anova.num_moves.few %>% summary()
tukey.num_moves.all
tukey.num_moves.few
tukey.num_moves.all %>% plot()
title(main = "number of moves (all)", line = 1)
tukey.num_moves.few %>% plot() 
title(main = "number of moves (few)", line = 1) # Significant difference

#### Performance: Number of Seconds ####

# Data filtering
puzzle_stats %>% select(num_seconds) %>% unlist() %>% hist() # Highly skewed data, not great for ANOVA testing
max_seconds <- 120 # Limit "outliers" / tail end of distribution
puzzle_stats.few_seconds <- puzzle_stats %>% filter(num_seconds <= max_seconds)
puzzle_stats.few_seconds %>% select(num_seconds) %>% unlist() %>% hist() # Improved distribution
nrow(puzzle_stats.few_seconds) / nrow(puzzle_stats) # Proportion of original data
# Box plots
puzzle_stats %>% ggplot(aes(x = protocol.user, y = num_seconds)) + geom_boxplot()
puzzle_stats.few_seconds %>% ggplot(aes(x = protocol.user, y = num_seconds)) + geom_boxplot() # Cut out most outliers
# Tests
anova.num_seconds.all <- aov(num_seconds ~ protocol.user, data = puzzle_stats)
anova.num_seconds.few <- aov(num_seconds ~ protocol.user, data = puzzle_stats.few_seconds)
tukey.num_seconds.all <- TukeyHSD(anova.num_seconds.all)
tukey.num_seconds.few <- TukeyHSD(anova.num_seconds.few)
# Stats
anova.num_seconds.all %>% summary()
anova.num_seconds.few %>% summary()
tukey.num_seconds.all
tukey.num_seconds.few
tukey.num_seconds.all %>% plot()
title(main = "number of seconds (all)", line = 1)
tukey.num_seconds.few %>% plot() 
title(main = "number of seconds (few)", line = 1) # Significant difference

#### Performance: Score ####

# Data filtering
puzzle_stats %>% select(score) %>% unlist() %>% hist()
# Box plots
puzzle_stats %>% ggplot(aes(x = protocol.user, y = score)) + geom_boxplot()
# Tests
anova.score.all <- aov(score ~ protocol.user, data = puzzle_stats)
tukey.score.all <- TukeyHSD(anova.score.all)
# Stats
anova.score.all %>% summary()
tukey.score.all
tukey.score.all %>% plot()
title(main = "score (all)", line = 1)

#### Performance: Bonus Compensation ####

# Data wrangling
protocol_users <- users %>% filter(!is.na(protocol))
# Data filtering
protocol_users %>% select(bonus_comp) %>% unlist() %>% hist() # Many users with no bonus
protocol_users.bonus <- protocol_users %>% filter(bonus_comp > 0)
protocol_users.bonus %>% select(bonus_comp) %>% unlist() %>% hist() # Improved distribution
nrow(protocol_users.bonus) / nrow(protocol_users) # Proportion of original data
# Box plots
protocol_users %>% ggplot(aes(x = protocol, y = bonus_comp)) + geom_boxplot()
protocol_users.bonus %>% ggplot(aes(x = protocol, y = bonus_comp)) + geom_boxplot()
# Tests
anova.bonus_comp.all <- aov(bonus_comp ~ protocol, data = protocol_users)
anova.bonus_comp.few <- aov(bonus_comp ~ protocol, data = protocol_users.bonus)
tukey.bonus_comp.all <- TukeyHSD(anova.bonus_comp.all)
tukey.bonus_comp.few <- TukeyHSD(anova.bonus_comp.few)
# Stats
anova.bonus_comp.all %>% summary()
anova.bonus_comp.few %>% summary()
tukey.bonus_comp.all
tukey.bonus_comp.few
tukey.bonus_comp.all %>% plot()
title(main = "bonus compensation (all)", line = 1)
tukey.bonus_comp.few %>% plot() 
title(main = "bonus compensation (few)", line = 1) # Significant difference

#### Performance: Sections ####

analyze.sections <- function(sect, metric) {
  metric.df <- sections %>% 
    filter(section == sect) %>% 
    inner_join(users, join_by(mturk_id))
  
  protocol.data <- metric.df[, "protocol.y"]
  metric.data <- metric.df[, metric]
  # ANOVA
  a <- aov(metric.data ~ protocol.data)
  a %>% summary() %>% print()
  # Tukey's HSD
  a.thsd <- a %>% TukeyHSD()
  a.thsd %>% print()
  a.thsd %>% plot()
  title(main = paste(sect, metric), line = 1)
  # Box plots
  ggplot(mapping = aes(x = protocol.data, y = metric.data)) + 
    geom_boxplot() + 
    ggtitle(sect) +
    ylab(metric)
}
analyze.sections("practice", "successes")
analyze.sections("practice", "num_puzzles")
analyze.sections("practice", "duration")
analyze.sections("testing", "successes")
analyze.sections("testing", "num_puzzles")
analyze.sections("testing", "duration")

#### Final Surveys ####

analyze.final_surveys <- function(metric) {
  metric.data <- final_surveys %>% 
    mutate(metric = rowSums(select(., starts_with(metric)))/3) %>% 
    inner_join(users, join_by(mturk_id))
  if (metric == "exp.power") {
    metric.data <- metric.data %>% filter(protocol != "none")
  }
  # ANOVA
  a <- aov(metric ~ protocol, data = metric.data)
  a %>% summary() %>% print()
  # Tukey's HSD
  a.thsd <- a %>% TukeyHSD()
  a.thsd %>% print()
  a.thsd %>% plot()
  title(main = metric, line = 1)
  # Box plots
  metric.data %>% ggplot(aes(x = protocol, y = metric)) +
    geom_boxplot() +
    ylab(metric)
}
analyze.final_surveys("sat.outcome")
analyze.final_surveys("sat.agent")
analyze.final_surveys("exp.power")
