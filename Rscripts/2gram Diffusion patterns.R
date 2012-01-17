setwd('/presidio/Rscripts')
rm(list=ls())
source("Rbindings.R")
source('Word Spread.R')
#First I flag some interesting words from the other computer.
#words has already been filled from 'Identify new words'
agedata = function(word) {
  f = genreplot(list(word),
            grouping='author_age',
            groupings_to_use = 63,
            counttype = 'Occurrences_per_Million_Words',
            ordering=NULL,
            years=c(1850,1922),
            smoothing=7,
            comparison_words = list(),
            words_collation='Case_Insensitive') + opts(title=word)
  f$data$birth = f$data$year-f$data$groupingVariable
  model = lm(ratio ~ year + birth,f$data,weights=nwords)
  list(plot=f,scores=summary(model)$coefficients[2:3,3])
}
            
mywords = words
models = lapply(words,agedata)
names(models) = mywords
scores = as.data.frame(t(sapply(models,'[[',2)))
plots = lapply(models,'[[',1)
names(plots)
scores$word = mywords
scores
scores$uppercase = grepl("[A-Z]",scores$word,perl=T)
models[['Total number']][[1]]
plobject = scores[!grepl("[A-Z]",scores$word,perl=T),]
  
#plobject$special = grepl("[A-Z]",scores$word,perl=T)
plobject = scores
plobject$facet=factor(plobject$uppercase)
plobject$length = cut(
  nchar(plobject$word),
  quantile(nchar(plobject$word), probs = seq(0, 1, 1/)),include.lowest=T)
levels(plobject$facet) = c("No uppercase letters","Has an uppercase letter")
levels(plobject$length) = paste("character length in",levels(plobject$length))
ratio <- ddply(plobject, .(facet,length), 
     function(x) c(score=
       paste(
         as.character(round(sum(x$year<x$birth)*100/sum(x$year > -100),1)),
         "%\nn=",
         sum(x$year > -100),sep=""
         ) ))
ratio$score

  
ggplot(plobject,aes(x=year,y=birth,label=word)) + 
  #geom_point(alpha=.1,color=muted('red')) +
  geom_hex() +
  geom_text(
    size=10,alpha=.5,
    aes(x=25,y=-5,label=score),
    data=ratio) + 
  geom_segment(aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  xlab("Strength of publication year effect (t-value)") + 
  facet_grid(length~facet)+
  opts(title=paste(
    "Selection of the top 10,000 non stopword-including two-grams with\nR > .75 and increase > 2x 1850-1922:\n",
    round(sum(plobject$year<plobject$birth)/nrow(plobject)*100,1),
                   "% of grams show greater effect\nfor author birth year than for publication year"))

  
scores$pos='unknown'
scores$pos[grep('tions?$',scores$word,perl=T)] = 'noun'
scores$pos[grep('ment?$',scores$word,perl=T)] = 'noun'
scores$pos[grep('ist$',scores$word,perl=T)] = 'adverb'
scores$pos[grep('ity$',scores$word,perl=T)] = 'noun'
scores$pos[grep('ed$',scores$word,perl=T)] = 'verb'
scores$pos[grep('ly$',scores$word,perl=T)] = 'adverb'
scores$pos[grep('al$',scores$word,perl=T)] = 'adjective'
scores$pos[scores$word %in% c("coal","metal")] = 'noun'
scores$pos=factor(scores$pos)
scores$nchar = factor(nchar(scores$word))
scores$IDF = words$IDF
scores$word[scores$pos=='unknown']
scores[c('word','pos')]
strReverse <- function(x) sapply(lapply(strsplit(x, NULL), rev), paste,
collapse="")
scores$word[order(strReverse(scores$word))]
strong = scores[scores$year > 10 | scores$birth > 10,]
scores$IDFquantile = cut(scores$IDF,quantile(scores$IDF),include.lowest=T)
scores$ncharquantile = cut(nchar(scores$word),quantile(nchar(scores$word)),include.lowest=T)

summary(scores$IDFquantile)
scores[is.na(scores$IDFquantile),]
?cut

?split

ggplot(scores) + geom_histogram(aes(x=IDF))
plotta = scores
ggplot(plotta,aes(x=year,y=birth,label=word)) + 
  #geom_point(alpha=.2) +
  geom_hex() + geom_rug(col=rgb(.5,0,0,alpha=.2)) + 
  #geom_text(size=3,alpha=.5) + 
  geom_segment(aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  xlab("Strength of publication year effect (t-value)") + 
  facet_grid(IDFquantile~ncharquantile,labeller=c(1:16)) + 
  opts(title=paste(sum(plotta$birth>plotta$year)/nrow(plotta), "% of words show greater effect\nfor author birth year than for publication year"))

models[['helpful']][[1]]

names(v) = mywords
v[[i]] + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub)

scores = sapply(v,function(item) {
  loc = summary(lm(ratio ~ year+groupingVariable,item$data,weights=nwords))$coefficients  
  c(loc[3,3],loc[2,3],loc[3,3]/loc[2,3])
})
as.data.frame(t(scores)) -> scores
rownames(scores) = mywords
names(scores) = c('age','year','slope')
ggplot(scores,aes(x=age,y=year,size=log(abs(slope)))) + geom_point()
v[['Then']]
abstractArt = v[['using']] + geom_contour(aes(z=ratio)) + ylab("") + xlab("") + opts(title="",legend.position = "none", axis.ticks = theme_blank(), axis.text.x = theme_blank(),axis.text.y = theme_blank())

lapply(verblist, function(words))

f = verblist[[1]]
f
#ageplot("nationwide")