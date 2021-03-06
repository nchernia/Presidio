#Attention Chapter
rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")

wordlist = list('attention')

  pairs = list(
    c("called","call"),
    c("excited","excite"),
    c("fixed","fix"),
    c("engaged","engage"),
    c("arrested","arrest"),
    c("awakened","awake"),
    c("concentration","concentrate"),
    c("aroused","arouse"),
    c("amusement","amuse"),
    c("compelled","compel"),
    c("confined","confine"))
silent =   lapply(pairs,function(pair) {
    dbGetQuery(con,paste("UPDATE wordsheap SET stem='",pair[2], "' WHERE stem='",pair[1],"'",sep=""))
  })

source("Rbindings.R")
source("ngrams wordgrid.R")
words = wordgrid(list("attention"),freqClasses=4,
    returnData=F,
    wordfield='casesens',
    field='word1',n=45, 
    yearlim=c(1800,2000)
  )

adunwords = c("absorbed", "amused", "aroused", "arrest", "arrests", "attract", 
"attracted", "attracting", "attracts", "attracts", "awaken","awake","awakened","call", "called", 
"calling", "calls", "challenge", "claimed", "command", "commanded", 
"commands", "compelled", "compelling", "compels", "concentrate", 
"concentrate", "concentrated", "confine","demand", "demanded", "demanding", "demands",
"devoted", "directed", "directing", "distract", "distracted", 
"diverted", "diverting", "divided", "draw", "drawing", "drawn", 
"draws", "drew", "enforce","engage","engaged", "escape","escaped","excited", "excite", "fix","focus", "gave", 
"giving", "increased", "increase","invite","merit", "need", "needed", "needing", 
"needs", "paid", "pay", "paying", "pays", "received", "receiving", 
"required", "riveted", "startled", "strained", "turn", 
"turn", "turned","wander", "wandering","withdraw")

adjectives = c("active", "anxious", "assiduous", "breathless", "careful", 
"child's", "close", "closer", "closest", "conscious", "considerable", 
"constant", "continuous", "critical", "deep", "deepest", "devout", 
"diligent", "direct", "divided", "divided", "due", "eager", "earnest", 
"enough", "entire", "especial", "exclusive", "expectant", "faithful", 
"favorable", "first", "fixed", "great", "his", "immediate", "increased", 
"increasing", "insufficient", "intelligent", "keen", "kind", 
"least", "less", "marked", "medical", "minute", "most", "much", "national", 
"ordinary", "our", "particular", "patient", 
"peculiar", "persevering", "personal", "polite", "principal", 
"profound", "prompt", "proper", "rapt", "renewed", "respectful", 
"rigid", "scant", "scrupulous", "sedulous", "serious", "slightest", 
"special", "special", "steady", "strained", "strict", "strictest", 
"sufficient", "sustained", "thoughtful", "undivided", "undue", 
"unremitted", "unremitting", "unwearied", "utmost", "vigilant", 
"voluntary", "watchful", "whole", "wide", "widespread")



adjectives = wordgrid(
  wordlist=list("attention")
         ,
         WordsOverride = adunwords
         ,
         collation='Case_Insensitive'
         ,
         n=80
         ,
         wordfield='stem',
         language = list('eng')
         ,
         yearlim=c(1823,2005)
         ,
         freqClasses = 4
         ,
         trendClasses=3
         ) 
wordgrid(list("God"),yearlim=c(1750,1922),freqClasses=4,trendClasses=3)


find_distinguishing_words <- function (
  word1,
  word2 = list('attention'),
  years = as.list(1820:1840),
  country = list("USA")
  ) {
  core_search = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list('lc1','catalog.bookid as id','catalog.nwords as length'),      
    words_collation = 'All_Words_with_Same_Stem',
    tablename='master_bigrams',
    search_limits = 
      list(
        list(
          'alanguage'=list('eng'),
          'word2' = word2,
          'word1' = word1,
          'country' = list("USA"),
          'year'    = years
          )
    )
  )
  #Now we flag the books that have the phrase 'call attention' before 1840,
  #and a baseline comparison of 1000 books.
  
  v = dbGetQuery(con,APIcall(core_search))
  flagBookids(v$id,1)
  flagRandomBooks(
    1000,
    2,
    paste(
      'year >= ',
      years[1],
      ' AND year <= ',
      rev(years)[1],
      " AND alanguage = 'eng' ",
      " AND (",
      paste("country='",country,"'",sep="",collapse = " OR "),
      ")"),
    preclear=F
    )
  v[order(v[,4]),]
  
  
  core_search = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list('words1.word as word'),      
    words_collation = 'All_Words_with_Same_Stem',
    tablename='master_bigrams',
    search_limits = 
      list(
        list(
          'bflag' = list(1)
          ),
        list(
          'bflag'  = list(2))
    )
  )
  z = compare_groups(core_search)
}

words = find_distinguishing_words(
  word1 = list('focus'),
  word2 = list('attention'),
  years = as.list(1915:1920),
  country = list("USA")
  )
  
words[[1]][1:25]


#What are the age patterns for 'pay attention' more frequently used 

limits = list("word1"=list("of"),"word2" = list("the"))
p = median_ages(limits)
z = median_ages(list("word"=list("smile")));z + geom_smooth(se=F,lwd=2,span=.3)

plot(z[,1],z[,2]-p[,2],type='l')
source('Word Spread.R')
genreplot(
    word = list('focus attention'),
    years = c(1830,1922),
    grouping = 'lc1',
    counttype = 'Occurrences_per_Million_Words',
    groupings_to_use=25,ordering=NULL,smoothing=7,
    comparison_words=list(),
    words_collation = "Case_Sensitive",
   country = list()) 
  genres  

genres =genreplot(list("waked"),
          grouping='author_age',
          groupings_to_use = 63,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1822,1922),
          smoothing=8,
          comparison_words = list("woke"),
          words_collation='Case_Sensitive',country=list("USA"))

core_query = 
  list(method = 'counts_query',
      smoothingType="None",      
      groups = list(
        "words1.word as w1","words1.stem as stem1",
        "year","lc1","lc0","state","country","aLanguage","nwords"),                           
      search_limits = 
         list(
          'word2'=list('attention')
     ))

vals = dbGetQuery(con,APIcall(core_query))
normstemscore = ddply(vals,.(stem1),function(frame) {
  data.frame(average = mean(xtabs(frame$count~frame$year)/xtabs(frame$nwords~frame$year)))
})

