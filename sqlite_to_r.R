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
users %>% filter(mturk_id %in% c(dropped_ids)) %>% nrow()
demographics %>% filter(mturk_id %in% dropped_ids) %>% nrow()
sections %>% filter(mturk_id %in% dropped_ids, section == "practice") %>% nrow()
sections %>% filter(mturk_id %in% dropped_ids, section == "testing") %>% nrow()
final_surveys %>% filter(mturk_id %in% dropped_ids) %>% select(mturk_id) %>% nrow()

#### Bonus Compensation ####

users %>% 
  select(mturk_id, completion_code, bonus_comp) %>% 
  tail(26) %>% 
  filter(bonus_comp > 0) %>%
  arrange(mturk_id)

#### Protocols ####

users %>% select(protocol) %>% table()

#### Demographics ####

demographics$chess.skill %>% table()

sections %>% 
  filter(section == "testing") %>% 
  inner_join(demographics, join_by(mturk_id)) %>% 
  ggplot(aes(x = chess.skill, y = successes)) + 
  geom_boxplot() + 
  ylab("successes")

demographics %>% 
  inner_join(sections, join_by(mturk_id)) %>% 
  filter(section == "practice") %>% 
  mutate(add.info.page = start_time - timestamp) %>% 
  select(add.info.page) %>% unlist() %>% unlist() %>% log10() %>% hist()

#### Performance ####

sections.analyze <- function(sect, metric) {
  metric.df <- sections %>% 
    filter(section == sect) %>% 
    inner_join(users, join_by(mturk_id))
  
  protocol.data <- metric.df[, "protocol.y"]
  metric.data <- metric.df[, metric]
  
  # aov(metric.data ~ protocol.data) %>% summary() %>% print()
  # aov(metric.data ~ protocol.data) %>% TukeyHSD() %>% print()
  # aov(metric.data ~ protocol.data) %>% TukeyHSD() %>% plot()
  # title(main = paste(sect, metric), line = 1)
  
  ggplot(mapping = aes(x = protocol.data, y = metric.data)) + 
    geom_boxplot() + 
    ggtitle(sect) +
    ylab(metric)
}
sections.analyze("practice", "successes")
sections.analyze("practice", "num_puzzles")
sections.analyze("practice", "duration")
sections.analyze("testing", "successes")
sections.analyze("testing", "num_puzzles")
sections.analyze("testing", "duration")

moves.stats <- moves %>% 
  group_by(section_id, puzzle_id, move_num, mistake) %>% 
  summarize(attempts = n(), time = sum(duration)) %>% 
  group_by(section_id, puzzle_id, move_num) %>% 
  summarize(correct = sum(!mistake), attempts = sum(attempts), time = sum(time)) 

puzzles.stats <- moves.stats %>% 
  group_by(section_id, puzzle_id) %>% 
  summarize(num_correct = sum(correct), attempts = sum(attempts), mistakes = attempts - num_correct, time = sum(time)) %>% 
  ungroup() %>% 
  inner_join(sections, join_by(section_id == id)) %>% 
  inner_join(users, join_by(mturk_id), suffix = c(".section", ".user")) %>% 
  select(mturk_id, section_id, section, puzzle_id, num_correct, attempts, mistakes, time, protocol.user)

#### Final Surveys ####

final_surveys %>% 
  inner_join(users, join_by(mturk_id)) %>% 
  filter(protocol == "none") %>% 
  select(sat.agent.3) %>% unlist() %>% 
  hist(seq(.5,7.5))

final_surveys.analyze <- function(metric) {
  metric.data <- final_surveys %>% 
    mutate(metric = select(., starts_with(metric)) %>% rowSums()/3) %>% 
    inner_join(users, join_by(mturk_id))
  
  # aov(metric ~ protocol, data = metric.data) %>% summary() %>% print()
  # aov(metric ~ protocol, data = metric.data) %>% TukeyHSD() %>% print()
  # aov(metric ~ protocol, data = metric.data) %>% TukeyHSD() %>% plot()
  # title(main = metric, line = 1)

  metric.data %>% ggplot(aes(x = protocol, y = metric)) +
    geom_boxplot() +
    ylab(metric)
}

final_surveys.analyze("sat.outcome")
final_surveys.analyze("sat.agent")
final_surveys.analyze("exp.power")

#### Feedback ####

feedback %>% select(text, mturk_id) %>% print(n=200)

