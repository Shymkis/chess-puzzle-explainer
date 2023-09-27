rm(list=ls())

library(RSQLite)
library(dplyr)
library(jsonlite)
library(ggplot2)

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

#### Obtain and clean SQLite table data frames ####

table_dfs <- get_table_dfs("application.db")

explanations <- table_dfs$explanation
explanations$protocol <- explanations$protocol %>% ordered(levels=c("none", "placebic", "actionable"))

moves <- table_dfs$move %>% filter(start_time > start_date, mturk_id %>% startsWith("A"))
moves$start_time <- moves$start_time %>% as.POSIXct()
moves$end_time <- moves$end_time %>% as.POSIXct()
moves$mistake <- moves$mistake %>% as.logical()

puzzles <- table_dfs$puzzle
puzzles$theme <- puzzles$theme %>% as.factor()

sections <- table_dfs$section %>% filter(start_time > start_date, mturk_id %>% startsWith("A"))
sections$section <- sections$section %>% as.factor()
sections$protocol <- sections$protocol %>% ordered(levels=c("none", "placebic", "actionable"))
sections$start_time <- sections$start_time %>% as.POSIXct()
sections$end_time <- sections$end_time %>% as.POSIXct()

surveys <- table_dfs$survey %>% filter(timestamp > start_date, mturk_id %>% startsWith("A"))
surveys$timestamp <- surveys$timestamp %>% as.POSIXct()

users <- table_dfs$user %>% filter(start_time > start_date, mturk_id %>% startsWith("A"))
users$experiment_completed <- users$experiment_completed %>% as.logical()
users$failed_attention_checks <- users$failed_attention_checks %>% as.logical()
users$start_time <- users$start_time %>% as.POSIXct()
users$end_time <- users$end_time %>% as.POSIXct()
users$consent <- users$consent %>% as.logical()
users$protocol <- users$protocol %>% ordered(levels=c("none", "placebic", "actionable"))

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

#### Check for Dropped Users ####

dropped_ids <- users %>% filter(experiment_completed == F) %>% select(mturk_id) %>% unlist()
users %>% filter(mturk_id %in% c(dropped_ids))
demographics %>% filter(mturk_id %in% dropped_ids)
sections %>% filter(mturk_id %in% dropped_ids)
moves %>% filter(mturk_id %in% dropped_ids)
final_surveys %>% filter(mturk_id %in% dropped_ids)
feedback %>% filter(mturk_id %in% dropped_ids)

#### Compensation Check ####

users %>% select(mturk_id, completion_code, compensation, end_time)

#### Performance Results ####

sections.results <- function(sect, metric) {
  sections %>% 
    inner_join(users, join_by(mturk_id)) %>% 
    filter(experiment_completed == T, section == sect) %>% 
    ggplot(aes(x = protocol.y, y = {{metric}})) + geom_boxplot() + ggtitle(sect)
}
sections.results("practice", successes)
sections.results("practice", duration)
sections.results("testing", successes)
sections.results("testing", duration)

#### Final Survey Stats ####

final_surveys.boxplot <- function(metric) {
  final_surveys %>% 
    inner_join(users, join_by(mturk_id)) %>% 
    filter(experiment_completed == T) %>% 
    mutate(metric = select(., starts_with(metric)) %>% rowSums()/3) %>% 
    ggplot(aes(x = protocol, y = metric)) + geom_boxplot() + ylab(metric)
}
final_surveys.boxplot("sat.outcome")
final_surveys.boxplot("sat.agent")
final_surveys.boxplot("exp.power")
