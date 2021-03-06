#! usr/bin/perl
use strict;
use warnings;

#This is a perl script that accepts text from STDIN and tokenizes it in a human readable format that serves as a good interchange for serious data parsing. It is optimized for use with Internet Archive books, but may have problems with them. It attempts to follow the rules for tokenizing laid out in the Michel-Aiden supplemental materials in science, using whitespace as a delimiter between words; in addition, it attempts to use English language punctuation rules to identify the ends of sentences and indicates those using a newline character. --Ben Schmidt

my @z = <>;

##Google files start with boilerplate about the book being scanned by google: this figures out how to ignore that.
my $googswitch = 0;
my $needs_goog_switch = 0;
my $linenumber = 0;


#Google books need the first page stripped because they have that first page included This will not work on things that contain the word "Google" legimately; them's the breaks, for now.
my $checkrange = 50;
if ($#z < $checkrange) {$checkrange = $#z} 

foreach my $i (0..$checkrange) {
    if ($z[$i] =~ m/Google/) {
	$needs_goog_switch = 1;
    }
}

#This just ignores the ones that are HTML junk.
if ($z[0] =~ m/html/) {
    $needs_goog_switch = 1;
}


print " ";


foreach my $line (@z) {
    $linenumber++;
    if ($googswitch == 1 || $needs_goog_switch == 0) {
	#The order of these regexes are important
	my $upper_case_letters = $line =~ tr/A-Z//;
	if ($upper_case_letters/length($line) >= 0.5) {
	    $line = "";
	}
#DROPPING OUT CAPITALIZED LINES ELIMINATES A _LOT_ OF JUNK HEADERS
	$line =~ s/-\s*[\n\r]//g; #hyphenated words at lineend shouldn't even have spaces
	$line =~ s/[\n\r]/ /g; #remove newlines, replaces with spaces.
	$line =~ s/\t\f/ /g; #replace tabs and formfeeds with spaces--the awk counts on the text having NO TABS AT ALL.
	#And I'm reserving \f to myself to mark sentence breaks.
	#$line =~ tr/[A-Z]/[a-z]/; #Set to lowercase--I'M GOING TO SWITCH THIS TO THE LATER SCRIPT
	$line =~ s/([\.\?!])(["'\)])/$2$1/g;
#Move period to end of sentence
	$line =~ s/([\.\?!])(["'\)])/$2$1/g; #Move period to end of sentence again, in case there's double quotes or a period and parenthesis or something";
        $line =~ s/([\.!\?]) +/$1\f/g; #replace sentence punctuation with formfeed--this is still bad with abbreviations, maybe I need a longer list of exceptions?
	$line =~ s/([\.!\?])$/$1\f/g; #Punctuation can come at the end of the line, too; but not in between characters.
     ##COMMON ABBREVIATIONS NOT TO END SENTENCES ON
     #needs to deal smarter with multiple consecutive things like this, but the /gi option is not working as it is supposed to.:
        $line =~ s/(\W)([A-Z]\.)\f/$1$2 /gi;
        $line =~ s/(\W)([A-Z]\.)\f/$1$2 /gi;
        $line =~ s/(\W)([A-Z]\.)\f/$1$2 /gi;
       	$line =~ s/\b(mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\.\f/ $1\. /gi; #Abbreviations can start with a newline as well as a space.                        	
        $line =~ s/\b(mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\.\f/ $1\. /gi; #Abbreviations can start with a newline as well as a space.                        
        $line =~ s/\b(mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\.\f/ $1\. /gi; #Abbreviations can start with a newline as well as a space.                        
  	$line =~ s/^.*digitize?d?.? by.*$//gi;                       
			      $line =~ s/^.*([vli]j|[gq])oo[gqs] ?[il1][ce].*$//gi; #kill any lines that have Google-matching keywords in them.
			      $line =~ s/^.*googl.*$//gi; #kill any lines that have Google-matching keywords in them.
		$line =~ s/([ \f!\?@%^*\(\)\[\]\-=\{\}\|\\:;<>,\/~`"#\+])/ $1 /g; #Surround punctuators with spaces`
		$line =~ s/'([^s])/ ' $1/gi; #single quotes aren't separators when part of possessive
		$line =~ s/\$([^\d])/ \$ $1/gi; #dollar signs aren't separators when preceding numerals.
			      $line =~ s/([^\d])\.([^\d])/$1 \. $2/gi; #Periods aren't separators when part of decimal numbers.
			      $line =~ s/\.$/ \./gi;# (Make sure to space out periods at end of line
                #UNIMPLEMENTED RULES
                #Hashes aren't separators when following a-g,j or x
		#
		$line =~ s/  +/ /g; #Replace multiple spaces with a single space
		$line =~ s/ ?\f ?/\n/g; #put newlines at the end of sentences, and strip surrounding spaces
		print "$line";
		       
	}
	if ($line =~ m/[gq]oo[gq][li1]e\W*com/gi) {$googswitch = 1;}# $switchedat = $linenumber; print "Switching:\t"}
}
