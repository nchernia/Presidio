#!/usr/bin/python
# -*- coding: utf-8 -*-

#UNIVERSAL SETTINGS

import MySQLdb
import re
import subprocess
from subprocess import call
import os
from datetime import datetime

#CHAUCER SETTINGS:
if True:
    project_directory = "/presidio"
    texts_directory = "/group/culturomics/books"
    downloads_directory = "/home/bschmidt/IA"
    mysql_directory = "/var/lib/mysql/data/presidio"
    cnx = MySQLdb.connect(read_default_file="~/.my.cnf",use_unicode = 'True',charset='utf8',db = "presidio")
    cursor = cnx.cursor()
    cursor.execute("SET NAMES 'utf8'")
    #import nltk
    import json
    from nltk import PorterStemmer
    from datetime import datetime

#WUMPUS SETTINGS:
if False:
    project_directory = '/home/bschmidt/Internet_Archive'
    texts_directory = '/group/culturomics/books'
    downloads_directory = '/group/culturomics/books/Downloads'
    mysql_directory = ''
    cnx = MySQLdb.connect(host='melville.seas.harvard.edu',user='bschmidt',passwd='newton',db='presidio',use_unicode = 'True',charset='utf8')
    cursor = cnx.cursor()
    cursor.execute("SET NAMES 'utf8'")

####### FUNCTIONS DEALING WITH WORD LISTS #######
def load_1grams_table(): #Get the onegrams lists of words into the database.
    import os
    cursor.execute("""CREATE TABLE 1grams (
        word VARCHAR(255), INDEX (word),
        year MEDIUMINT,
        words INT,
        pages INT,
        books INT);""")
    cursor.execute("""ALTER TABLE 1grams disable keys""")
    for file in os.listdir(downloads_directory + '/ngrams'):
        print "Working on loading " + file
        name = downloads_directory + '/ngrams/' + file
        cursor.execute("LOAD DATA LOCAL INFILE '" + name + "' INTO TABLE 1grams FIELDS TERMINATED BY '\t';")
    print "Loading Complete: Enabling indexes..."
    cursor.execute("""ALTER TABLE 1grams enable keys""")

def load_ngrams_word_list_as_new_sql_file(): #This is a version that has been parsed in perl to have common words.
    print "Loading ngrams wordlist as SQL file..."
    #call("perl " + project_directory + "/perlscripts/ngramsparser.pl " + downloads_directory + '/ngrams',shell=True)
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS words (
        wordid MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, 
        word VARCHAR(255), INDEX (word),
        count BIGINT UNSIGNED,
        normcount FLOAT,
        books INT UNSIGNED,
        lowercase VARCHAR(255), INDEX (lowercase),
        stem VARCHAR(31), INDEX (stem),
        stopword TINYINT DEFAULT 0,
        include_in_counts TINYINT DEFAULT 0,
        charcode VARBINARY(32),
        ffix VARCHAR(255),
        casesens VARBINARY(255), INDEX(casesens),
        IDF FLOAT,
        PRIMARY KEY (wordid)
        );""")
    cursor.execute("ALTER TABLE words DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '""" + downloads_directory + "/sorted.txt" + """' INTO TABLE words (word,count,books,normcount,lowercase)""")
    print "building indexes"
    #Store the IDF values
    cursor.execute("""SET @a = (SELECT max(books) FROM words);""")
    cursor.execute("""UPDATE words SET IDF = log(@a/books);""")
    cursor.execute("ALTER TABLE words ENABLE KEYS")
    
def update_Porter_stemming(): #We use stems occasionally.
    "Updating stems from Porter algorithm..."
    from nltk import PorterStemmer
    stemmer = PorterStemmer()
    cursor.execute("""SELECT word FROM words WHERE wordid <= 750000 and stem is null;""")
    words = cursor.fetchall()
    for local in words:
        word = ''.join(local)
        if re.match("^[A-Za-z]+$",word):
            query = """UPDATE words SET stem='""" + stemmer.stem(''.join(local)) + """' WHERE word='""" + ''.join(local) + """';""" 
            z = cursor.execute(query)
        
def update_stopwords(): #I used to use this list of stopwords to keep some processes shorter
    "updating stopwords from nltk and my additions..."
    stopset = set(nltk.corpus.stopwords.words('english'))
    stopset.update(set(['one', 'may', 'would', 'upon', 'two', 'said', 'made', 'first', 'must', 'could', 'many', 'well', 'shall', 'much', 'like', 'us', 'also', 'every', 'without', 'even', 'part', 'make', 'place', 'found', 'people', 'way', 'three','never', 'yet', 'might', 'come', 'still', 'know', 'd', 'power', 'another', 'thus', 'last', 'right', 'though', 'take', 'given', 'called', 'de', 'came', 'however', 'among', 'give', 'far', 'present', 'whole', 'form', 'used', 'less', 'thought', 'use', 'name', 'year', 'left', 'order', 'back', 'always', 'ever', 'let', 'things', 'nothing', 'v', 'away', 'taken', 'p', 'per', 'therefore', 'whose', 'since', 'cannot', 'o', 'others', 'second', 'often', 'four', 'half', 'within','several', 'following', 'soon', 'almost','five','either', 'thing', 'b', 'st', 'hundred','whether', 'become', 'c', 'perhaps', 'n', 'enough', 'e']))
    import string
    letters = string.lowercase
    for lettera in letters:
        for letterb in letters:
            updated = lettera+letterb
            stopset.update([(updated)])
        stopset.update(lettera)
    for stopword in stopset:
        query = """UPDATE words SET stopword=1 WHERE word='""" + stopword + """';""" 
        z = cursor.execute(query)
        
####FUNCTIONS DEALING WITH LIBRARY CATALOGS#######

###CREATING CATALOGS
def update_catalog (latestOLcatalog = "2011-09-30"):
    #Works whether or not you have an open_editions table already, I think.
    if not os.path.exists(downloads_directory + "/Edition Data.txt"):
        print "Parsing Latest OL dump for editions data:"
        system_call = 'perl ' + project_directory+'/perlscripts/print\ OL\ works\ catalog\ to\ text\ file\ for\ import.pl ' + downloads_directory + '  ol_dump_editions_' + latestOLcatalog + '.txt ' +project_directory
        call(system_call ,shell=True)
    else:
        print "Edition Data already exists: not rescanning"
    print "Building SQL tables"
    cursor.execute("""DROP TABLE IF EXISTS OL_editions""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OL_editions (
    authorid VARCHAR(15), INDEX (authorid),
    editionid VARCHAR(15), INDEX (editionid),
    language CHAR(3),
    lc_classifications VARCHAR(23),
    lccn INT,
    ocaid VARCHAR(29), index (ocaid),
    oclc_numbers INT,
    publish_country CHAR(3),
    year SMALLINT,
    publish_places VARCHAR(127),
    publishers VARCHAR(127),
    title VARCHAR(255),
    workid VARCHAR(15), INDEX(workid),
    authorbirth SMALLINT,
    workyear SMALLINT,
    author VARCHAR(255) )
    """)

    cursor.execute("LOAD DATA LOCAL INFILE '" + downloads_directory + "/Edition Data.txt" + "' INTO TABLE OL_editions (ocaid ,title ,publish_country , year , lc_classifications ,oclc_numbers ,    lccn ,    publish_places ,    publishers ,    language ,    editionid ,    authorid,    workid);")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_editions (
    authorid VARCHAR(15), INDEX (authorid),
    editionid VARCHAR(15), INDEX (editionid),
    language CHAR(3),
    lc_classifications VARCHAR(23),
    lccn INT,
    ocaid VARCHAR(29), index (ocaid),
    oclc_numbers INT,
    publish_country CHAR(3),
    year SMALLINT,
    publish_places VARCHAR(127),
    publishers VARCHAR(127),
    title VARCHAR(255),
    workid VARCHAR(15),INDEX(workid),
    authorbirth SMALLINT,
    workyear SMALLINT,
    author VARCHAR(255),
    bookid MEDIUMINT UNSIGNED,
    nwords INT,
    ngrams INT,
    volume TINYINT,
    subset VARCHAR(31), INDEX (subset),
    country VARCHAR(255),
    state CHAR(2),
    author_age SMALLINT,
    city VARCHAR(255),
    lc0 CHAR(1),
    lc1 CHAR(2),
    lc2 SMALLINT,
    aLanguage VARCHAR(31),
    duplicate TINYINT,
    PRIMARY KEY (bookid)
    ) CHARACTER SET 'utf8';    """)

    #SET UP AND UPDATE A MASTER LIST OF BOOKIDs (So we can have a 3-bit persistent identifier)
    cursor.execute("""CREATE TABLE IF NOT EXISTS bookid_master (bookid MEDIUMINT AUTO_INCREMENT,editionid VARCHAR(15), INDEX (editionid),PRIMARY KEY (bookid))""")
    #Fill with any old entries from open_editions with their old bookids
    cursor.execute("""INSERT INTO bookid_master (bookid,editionid)
                      SELECT t1.bookid,t1.editionid from open_editions as t1 LEFT JOIN bookid_master
                      USING (bookid) where bookid_master.bookid is null;""")
    #Create new entries for the editionids that aren't already in bookid_master
    cursor.execute("""INSERT INTO bookid_master (editionid) SELECT t1.editionid FROM OL_editions as t1 LEFT JOIN bookid_master as t2 USING (editionid) WHERE t2.editionid is null""")
    #Then we can just insert any new rows from OL_editions into a new table;
    cursor.execute( """CREATE TABLE tmp (SELECT bookid,OL.*,nwords,ngrams,volume,subset,country,state,author_age,city,lc0,lc1,lc2,aLanguage,duplicate FROM OL_editions as OL JOIN bookid_master USING (editionid) LEFT JOIN open_editions USING (bookid))""") 
    #And build up a new master catalog while checking to make sure there are no duplicate bookids (which OL_editions CAN HAVE)
    cursor.execute( """CREATE TABLE master_catalog LIKE tmp""")
    cursor.execute(""" ALTER TABLE master_catalog ADD PRIMARY KEY (bookid)""")
    for mystring in ["ocaid","bookid","editionid","subset","lc_classifications","workid"]:
        cursor.execute("""ALTER TABLE master_catalog ADD INDEX (""" + mystring + """)""")
    cursor.execute("""INSERT IGNORE INTO master_catalog SELECT * from tmp;""")
    cursor.execute("""drop table tmp;""")
    cursor.execute("""DROP TABLE open_editions""")
    cursor.execute("""RENAME TABLE master_catalog TO open_editions""")

    add_author_dates(latestOLcatalog=latestOLcatalog,downloads_directory = downloads_directory+"/Catinfo")
    add_work_dates(latestOLcatalog=latestOLcatalog,downloads_directory = downloads_directory+"/Catinfo")
    add_split_lc_fields()

def create_LCSH_table(editionsloc = downloads_directory + "/LCSH.txt"):
    queryString = """
     CREATE TABLE IF NOT EXISTS subject_headings (
     editionid VARCHAR(15),
     h1 VARCHAR(2045),INDEX (h1),
     h2 VARCHAR(255),
     h3 VARCHAR(255),
     h4 VARCHAR(255),
     h5 VARCHAR(255),
     h6 VARCHAR(255),
     h7 VARCHAR(255),
     h8 VARCHAR(255),
     bookid MEDIUMINT UNSIGNED, INDEX (bookid)
     ) CHARACTER SET 'utf8';    """
    print queryString
    cursor.execute(queryString)
    cursor.execute("""ALTER TABLE subject_headings DISABLE KEYS""")
    cursor.execute("""LOAD DATA LOCAL INFILE '""" + editionsloc + """' INTO TABLE subject_headings""")
    cursor.execute("""UPDATE subject_headings 
                      SET bookid = (SELECT open_editions.bookid from open_editions
                      WHERE open_editions.editionid=subject_headings.editionid)""")
    print "enabling keys"
    cursor.execute("""ALTER TABLE subject_headings ENABLE KEYS;""")

def add_author_dates (latestOLcatalog="2011-9-30",downloads_directory = ""):
    print "ADDING AUTHOR DATES..."
    filehandle  = open(downloads_directory + "/ol_dump_authors_"+ latestOLcatalog + ".txt",'r')
    authorlist = set()
    print "Loading information from catalog to parse..."
    cursor.execute("SELECT authorid,editionid FROM OL_editions WHERE author is NULL")
    print "Storing catalog information..."
    for entry in cursor:
        authorlist.add(entry[0])
    print "Loading information from file into database..."
    for myline in filehandle:
        myline = myline.split("\t")
        id = re.sub(".*/","",myline[1])
        if id in authorlist:
            info = json.loads(myline[4])
            name = ""
            birth = "NULL"
            if ('name' in info):
                name = info['name']
                name = mysql_protect(name)
            if 'birth_date' in info:
                birth = info['birth_date']
                birth = extract_year(birth)
            if name != "":
                sql_string = 'UPDATE open_editions SET author="' +name+ '", authorbirth='+birth+' WHERE authorid="' + id + '"'
                cursor.execute(sql_string) 
    cursor.execute("""UPDATE open_editions as open,OL_editions as OL SET open.authorbirth = OL.authorbirth, open.author = OL.author WHERE OL.author IS NOT NULL;""")
    cursor.execute("""UPDATE open_editions set author_age = year - authorbirth""")

def add_work_dates (latestOLcatalog="2011-07-31",downloads_directory = "/home/bschmidt/IA/Catinfo"):
    print "ADDING WORK DATES..."
    filehandle  = open(downloads_directory + "/ol_dump_works_"+ latestOLcatalog + ".txt",'r')
    authorlist = set()
    print "Loading information from catalog to parse..."
    cursor.execute("SELECT workid,editionid FROM OL_editions where workyear is NULL")
    print "Storing catalog information..."
    for entry in cursor:
        authorlist.add(entry[0])
    print "Loading information from file into database..."
    for myline in filehandle:
        myline = myline.split("\t")
        workid = re.sub(".*/","",myline[1])
        if workid in authorlist:
            info = json.loads(myline[4])
            year = "NULL"
            if 'first_publish_date' in info:
                year = info['first_publish_date']
                year = extract_year(year)
            sql_string = 'UPDATE OL_editions SET workyear='+year+' WHERE workid="' + workid + '"'
            cursor.execute(sql_string)
    cursor.execute("""UPDATE open_editions as open,OL_editions as OL SET open.workyear = OL.workyear WHERE OL.workyear IS NOT NULL;""")
    

def mysql_protect(string):
    #Occasionaly, I insert queries into MySQL that have unpermitted text characters in them. This should fix that.
    text = string.replace('''\\''','''\\\\''')
    text = text.replace('"','\\"')
    return text

def add_split_lc_fields():
    print "loading classification data to parse"
    lcclasses = get_dict_from_mysql("SELECT editionid,lc_classifications FROM open_editions WHERE lc_classifications NOT LIKE '' and lc_classifications is not null and lc1 is null;")
    print "Splitting and saving LC codes"
    for edition in lcclasses.keys():
        lcclass = lcclasses[edition]
        lcclass = lcclass.encode("ascii",'replace')
        mymatch = re.match(r"^(?P<lc1>[A-Z]+) ?(?P<lc2>\d+)", lcclass)
        if (mymatch):
            silent = cursor.execute("UPDATE open_editions SET lc1='"+mymatch.group('lc1')+"',lc2="+mymatch.group('lc2')+" WHERE editionid='" + edition + "';")
    print "Indexing LC codes"
    cursor.execute("ALTER TABLE open_editions add index lc1 (lc1);")

def create_memory_tables():
    #There are three major types of memory tables we use; for words, for catalog information, and for non-unique catalog information. 
    #The first two are self-explanatory: the third is for things like subject headings which can exist for several forms for the same book.
    #The general tactic here is to build up the table in a separate location, and then only at the last minute replace the old one; that lets us do this while the database is live without disruptions.
    #Memory tables disappear on restart, 
    cursor.execute("drop table if exists tmpheap")
    cursor.execute("""CREATE TABLE tmpheap (
        wordid MEDIUMINT UNSIGNED NOT NULL,
        word VARCHAR(31), INDEX(word),
        stem VARCHAR(31), INDEX(stem),
        casesens VARBINARY(31), INDEX (casesens),
        lowercase VARCHAR(31),INDEX(lowercase),
        ffix VARCHAR(31), INDEX (ffix),
        IDF FLOAT,
        wflag TINYINT,
        PRIMARY KEY (wordid)) ENGINE = MEMORY""")
    cursor.execute("""INSERT INTO tmpheap (wordid,word,stem,casesens,lowercase,ffix,IDF) SELECT wordid,word,stem,casesens,lowercase,ffix,IDF FROM words where wordid <= 1000000;""")
    cursor.execute("drop table if exists wordsheap")
    cursor.execute("RENAME TABLE tmpheap to wordsheap")
    cursor.execute("""CREATE TABLE tmpheap (
        bookid MEDIUMINT UNSIGNED,
        year SMALLINT,
        lc1 CHAR(3),
        lc2 SMALLINT,
        nwords INT,
        publish_country CHAR(3),
        authorbirth SMALLINT,
        workyear SMALLINT,
        language CHAR(3),
        aLanguage VARCHAR(15),
        subset VARCHAR(10),
        country VARCHAR(15),
        state CHAR(2),
        author_age SMALLINT,
        lc0 CHAR(1),
        bflag TINYINT,
        PRIMARY KEY (bookid)) ENGINE = MEMORY""")
    cursor.execute("""INSERT INTO tmpheap (bookid,year,lc1,lc2,nwords,publish_country,authorbirth,workyear,language,aLanguage,subset,country,state,author_age,lc0) SELECT bookid,year,lc1,lc2,nwords,publish_country,authorbirth,workyear,language,aLanguage,subset,country,state,author_age,lc0 
FROM open_editions WHERE nwords > 0 AND duplicate != 1; """)
    cursor.execute("""DROP TABLE IF EXISTS catalog""")
    cursor.execute("RENAME TABLE tmpheap TO catalog")
    queryString = """
     CREATE TABLE tmpheap (
     bookid MEDIUMINT UNSIGNED, INDEX (bookid),
     LCSH VARCHAR(30)
    ) CHARACTER SET 'utf8' ENGINE = MEMORY;    """
    cursor.execute(queryString)
    cursor.execute("""INSERT INTO tmpheap 
    SELECT bookid,h1 as h FROM subject_headings JOIN catalog USING (bookid) WHERE h1 IS NOT NULL AND h1 != "" UNION
    SELECT bookid,h2 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h2 IS NOT NULL AND h2 != "" UNION
    SELECT bookid,h3 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h3 IS NOT NULL AND h3 != "" UNION
    SELECT bookid,h4 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h4 IS NOT NULL AND h4 != "" UNION
    SELECT bookid,h5 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h5 IS NOT NULL AND h5 != "" UNION
    SELECT bookid,h6 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h6 IS NOT NULL AND h6 != "" UNION
    SELECT bookid,h7 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h7 IS NOT NULL AND h7 != ""  UNION
    SELECT bookid,h8 as h  FROM subject_headings JOIN catalog USING (bookid) WHERE h8 IS NOT NULL AND h8 != "" ;""")
    cursor.execute("""DROP TABLE IF EXISTS LCSH""")
    cursor.execute("""RENAME TABLE tmpheap TO LCSH""")

##### FUNCTIONS DEALING WITH WORDCOUNT TABLES

def fix_place_metadata():
    print "Updating US and UK"
    cursor.execute("update open_editions set country = 'USA' WHERE country is null and SUBSTR(publish_country,3,1)='u';")
    cursor.execute("update open_editions set country = 'UK' WHERE SUBSTR(publish_country,3,1)='k' and country is null;")
    cursor.execute("update open_editions set state = publish_country WHERE SUBSTR(publish_country,3,1)='u' and state is null;")
    print "Updating common country codes"
    codes = {"ne":"Netherlands","au":"Austria","be":"Belgium", "ii":"India",'sz':"Switzerland","dk":"Denmark","po":"Portugal", "pl":"Poland","ru":"Russia","sw":"Sweden"}
    for code in codes:
        print "\t" + code
        cursor.execute("UPDATE open_editions set country = '" + codes[code] + "' WHERE publish_country = '" + code + "' and country is null")
    World_Cities = {"Oxford":"UK", "London":"UK", "Paris":"France","Leipzig":"Germany","Berlin":"Germany", "Tokyo":"Japan","Edinburgh":"UK","Lisboa":"Portugal","Bruxelles":"Belgium", "Madrid":"Spain","Wien":"Austria","Milano":"Italy","Budapest":"Hungary","Stuttgart":"Germany","Buenos Aires":"Argentina","Firenze":"Italy","Lipsiae":"Germany"}
    print "Fixing word Cities"
    for city in World_Cities.keys():
        print "\t" + city
        versions = ["_" + city,city,city+"%","_"+city+"%"]
        for version in versions:
            cursor.execute("UPDATE open_editions SET country = '" + World_Cities[city] + "' WHERE country is null and publish_places LIKE '" + version + "'")
    US_Cities = {"New York":"NY","New-York":"NY","Cincinatti":"OH","Boston":"MA","Chicago":"IL","Philadelphia":"PA"}
    print "Fixing US cities"
    for city in US_Cities.keys():
        print "\t" + city
        versions = ["_" + city,city,city+"%","_"+city+"%"]
        for version in versions:
          cursor.execute("UPDATE open_editions SET country = 'USA' WHERE country is null and publish_places LIKE '" + version + "'")  
          cursor.execute("UPDATE open_editions SET state = '" + US_Cities[city] + "' WHERE state is null and publish_places LIKE '" + version + "'")

def alert_duplicate_editions():
    #This doesn't match the open library spec, but they have a lot of duplicate editions. So I only allow one copy of every workid-year combination, IF there's definitely two copies of the work. The problem is that this means I spend a lot of time creating indexes even if I have duplicated books... Ah well.
    cursor.execute("""DROP TABLE IF EXISTS duplicates""")
    print "Finding duplicates based on workid and year"
    cursor.execute("""CREATE TABLE duplicates (bookid MEDIUMINT UNSIGNED) ENGINE=MEMORY;""")
    cursor.execute("""INSERT INTO duplicates SELECT t1.bookid FROM open_editions t1 JOIN open_editions t2 USING (year,workid) WHERE workid is not null and workid != "" and t1.nwords > 0 and t2.nwords > 0 AND t1.bookid > t2.bookid GROUP BY t1.bookid;""")
    print "updating open_editions table"
    cursor.execute("""UPDATE open_editions SET duplicate=0""")
    cursor.execute("""UPDATE open_editions as t1 , duplicates as t2 SET t1.duplicate=1 where t1.bookid = t2.bookid""")
    cursor.execute("""DROP TABLE duplicates""")

def more_duplicate_alerts():
    cursor.execute("""SELECT title,year,count(*) as count FROM open_editions WHERE duplicate = 0 and nwords > 0 AND title != "" AND title != "Works." AND title != "Poems" AND title != "Abraham Lincoln" AND title != "Publications." AND CHAR_LENGTH(title) > 1 GROUP BY title,year HAVING count > 30 ORDER BY count;""")
    fetched = cursor.fetchall()
    for row in fetched:
        title = row[0]
        import re
        if not re.search("'",title):
            cursor.execute("""UPDATE open_editions SET duplicate = 1 WHERE title = '""" + title + """';""")

def create_master_bigrams():
    cursor.execute("""UPDATE words SET ffix = "1" WHERE word='"' OR word="." OR word = "-" OR word = "(" OR word = ")" OR word = ";" OR word = "'" OR word = ":" OR word = "?" OR word = "/" OR word = "!" OR word = "[" OR word = "]" OR word = "{" OR word = "}" OR word = "*" OR word = "^" OR word = "=" OR word = "+" OR word = "|" OR word = "~" OR word = "|" OR word = "_" OR word = "—" OR word = "»" OR word = "«" OR word ="•";""")
    #create_memory_tables()
    for subset in ["fre","ger","etc","uuu","eng"]:
        cursor.execute("""INSERT INTO master_bigrams SELECT bg.bookid,word1,word2,count FROM """ + subset + """_bigrams as bg JOIN wordsheap as w1 JOIN wordsheap AS w2 JOIN catalog as cat  ON cat.bookid = bg.bookid AND w1.wordid=word1 AND w2.wordid=word2 WHERE w1.ffix is null AND w2.ffix is null;""")

def get_dict_from_mysql(query):
    #turns a MySQL query into a set of key-value pairs. Super-useful, super-easy.
    cursor.execute(query)
    mydict = dict(cursor.fetchall())
    return mydict
    
def create_mergetable(libname,tabletype,component_tables):
    create_counttable(libname,tabletype,suffix = "",engine = """MERGE UNION=(
    """ + ','.join(component_tables) + """)
    INSERT_METHOD = NO""",disable_keys=False)

def enable_indexes(libname):
    for type in ["bookcounts","booktext","sentencecounts"]:
        print str(datetime.now()) + "\tBUILDING INDEXES ON " + type
        tablelist = get_matching_tables(libname + "_" + type)
        for table in tablelist:
            cursor.execute("ALTER TABLE " + table + " ENABLE KEYS")

def myisam_pack(libname,mysql_directory):
    #Compressing tables saves a lot of space (usually down to 33%) but requires that they be read only. 
    for type in ["bookcounts","sentencecounts"]:
        print str(datetime.now()) + "\tPACKING TABLES IN " + type
        tablelist = get_matching_tables(libname + "_" + type)
        for table in tablelist:
            call( "myisampack -s " + mysql_directory + "/" + table + ".MYI",shell=True)
#            call( "myisamchk -rq " + mysql_directory + "/" + table + ".MYI",shell=True) #This seems to screw things up somehow, so I don't call it anymore


def get_matching_tables(searchstring):
    #This can be helpful to check if tables exists for various reasons
    silent = cursor.execute("show tables;")
    tablelist = [item[0] for item in cursor.fetchall()]
    tablelist = filter(re.compile(searchstring).search,tablelist)
    return tablelist

def create_master_bookcounts():
    cursor.execute("""CREATE TABLE IF NOT EXISTS master_bookcounts LIKE eng_bookcounts""")
    cursor.execute("""ALTER TABLE master_bookcounts DISABLE KEYS""")
    for subset in ["ger","etc","fre","uuu","eng"]:
        print "working on " + subset + " at " + str(datetime.now())
        cursor.execute("""INSERT INTO master_bookcounts SELECT bookid,wordid,count FROM """ + subset + "_bookcounts JOIN catalog USING (bookid)""")
    print "Enabling keys at " + str(datetime.now()) 
    cursor.execute("""ALTER TABLE master_bookcounts ENABLE KEYS""")
    print "all done at " + str(datetime.now())

#####GENERAL TEXT PROCESSING

def extract_year(string):
    years = re.findall("\d\d\d\d",string)
    if(years):
        return years[0]
    else:
        return "NULL"

class SQLquery:
    def __init__(self,querystring):
        self.query = querystring
    def execute(self):
        cursor.execute(self.query)
        self.results = cursor.fetchall()
    def display(self):
        self.execute()
        for line in self.results:
            print "\t".join([str(element) for element in line])

            


#######GENERAL SQL FUNCTIONS

def MySQL_insert(table,columns,data):
    #Note: I'm taking data as a list of strings, since a list of lists would create all sorts of funny typing problems with numbers and characters
    string = """INSERT INTO """ + table + "(" + columns + ") " + "VALUES " + ", ".join(data)
    return string

def delete_matching_database_tables(string,really = False): #Dangerous!
    if really==True:
        tablelist = get_matching_tables(string)
        for table in tablelist:
            cursor.execute("drop table " + table)

#### NOTEPAD
def update_word_counts(subset):
    cursor.execute("""update open_editions set nwords = (select sum(count) as count from """ + subset + """_bookcounts as bookcounts where open_editions.bookid = bookcounts.bookid) WHERE subset='""" + subset + """';""")
    #This updates the open_editions nwords field from the database itself--quite a nice way to do it.
