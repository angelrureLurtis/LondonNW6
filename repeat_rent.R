library(McSpatial)
library(zoo)
#install.packages('data.table')
library(data.table)
#install.packages('gtools')
library(gtools)
library(purrr)

data <- read.csv('rent_data_agg.csv')

data$price <- log(data$Average)

repeat_sales <- function(df){
  
  if (nrow(df) < 3){
    return(list('NONE'))
  }
  
  rsdf <- repsaledata(df$price, df$Year, df$beds)
  
  if (nrow(rsdf) < 3){
    return(list('NONE'))
  }
  
  model <- repsale(rsdf$price0, rsdf$time0, rsdf$price1, rsdf$time1, graph = FALSE, print = FALSE)
  
  rsdf$deltat <- rsdf$time1 - rsdf$time0
  
  indexs = data.frame(model$pindex)
  indexs$deltat <- (1:length(indexs$model.pindex))
  
  rsdf <- merge(rsdf, indexs)
  
  rsdf$model.pindex <- na.locf(rsdf$model.pindex, fromLast = TRUE)
  
  rsdf$predi <- rsdf$price0+rsdf$model.pindex
  
  cor.test(rsdf$predi, rsdf$price1)
  
  return(model$pindex)
}

segment_beds <- function(df){
  
  i <- 1
  indexs_list <- list()
  for (n_beds in sort(unique(df$beds))) {
    subdata <- df[df$beds==n_beds,]
    indexs <- repeat_sales(subdata)
    indexs_list[i] <- list(indexs)
    i <- i + 1
  }
  return(indexs_list)
}

fix_lists <- function(nest_list) {
  
  lens <- unlist(map(.x = nest_list, .f = length))
  max_len <- max(lens)
  for (i in (1:length(nest_list))){
    if (length(nest_list[[i]])!=1 & length(nest_list[[i]])<max_len)
    {
      
      for (missing in (length(nest_list[[i]]):max_len))
      {
        nest_list[[i]][[paste('Time', missing, sep = ' ')]] <- 0
      }
      
      nest_list[[i]] <- data.frame(nest_list[[i]])
    }
  }
  df <- data.frame(nest_list)
  colnames(df) <- c(1:length(colnames(df)))
  return(df)
}

datas <- segment_beds(data)
datadf<-fix_lists(datas)
colnames(datadf) <- c(0:(length(colnames(datadf))-1))
rownames(datadf)[1] <- "Time 1"
write.csv(datadf, '.rri_index_per_bed_2011_to_2019.csv')
