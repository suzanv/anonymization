# python3 names.py dummy-sample.tab

# This script anonymizes the comment fields ('omschrijving') in Dutch bank transactions.
# It takes as input file a tab-separated text file with the following columns:
# MINISTERIE, BOEKJAAR, NAAM LEVERANCIER, OMSCHRIJVING, BEDRAG, VALUTA, GB_DATUM, EUR_BEDRAG

# It uses a number of external resources:
# - a list of 10,000 Dutch surnames and prefixes (‘de’, ‘ter’, ‘van’ etc.). Downloaded from http://www.naamkunde.net/?page_id=294
# - a list of 9,755 Dutch first names. Downloaded from http://www.naamkunde.net/?page_id=293
# - a list of 381,292 Dutch words. The file DFW.CD from the CELEX database https://catalog.ldc.upenn.edu/ldc96l14
# - a list of abbreviations, extracted from the transaction data itself: all words of 2–4 words that consist of only capital letters and are not a prefix or salutation (‘DHR’, ‘MEVR’, etc.), and occur at least 50 and that times in the data.5

# The generated output is a tab-separated file with the following 3 columns:
# item id of original row, anonymized omschrijving (names replaced by ***), list of found names

import sys
import re
#import operator
import json
import os
import xml.etree.ElementTree as ET
from random import randint

no_of_lines_read = 500000


datafilename = sys.argv[1]
json_ngrams_filename = "ngrams.json"
json_inverted_index = "ngram_inverted_index.json"
json_data_columns = "data_columns.json"

records_with_names_filename = "anonymized_omschrijvingen+names.out.tab"
maxn = 5

random_items = []
for k in range(0,200+1):
    random_item = randint(1,no_of_lines_read+1)
    random_items.append(random_item)
print (random_items)

def tokenize(t):
    #text = t.lower()
    # note that this function is very different from common tokenization functions because we need punctuation for recognizing names
    text = t
    text = re.sub("\n"," ",text)
    text = re.sub(r'<[^>]+>',"",text) # remove all html markup
    text = re.sub("\.",". ",text) # let . follow by whitespace for cases such as H.Ruissen
    text = re.sub("-","- ",text) # let . follow by whitespace for cases such as Advies-A.W. van Engen
    text = re.sub('[^a-zèéeêëėęûüùúūôöòóõœøîïíīįìàáâäæãåçćč&@#A-ZÇĆČÉÈÊËĒĘÛÜÙÚŪÔÖÒÓŒØŌÕÎÏÍĪĮÌ0-9/() \',.]', "", text)
    wrds = text.split()
    #print (wrds)
    return wrds


months = ("jan","januari","feb","februari","mrt","maart","apr","april","mei","jun","juni","jul","juli","aug","augustus",
          "sept","september","okt","oktober","nov","november","dec","december")

prefixes = set()
def initcaps(ngram):
    ngram_initcaps = ""
    words = ngram.split(" ")
    for word in words:
        #print(word)
        if word.lower() not in prefixes:
            ngram_initcaps += word.title() + " "
        else:
            #print(word.lower())
            ngram_initcaps += word.lower() + " "
    ngram_initcaps = ngram_initcaps.rstrip()
    #print(ngram,ngram_initcaps)
    return ngram_initcaps



print ("Read voornamenlijst")
firstnames = dict()
with open('voornamen_10kw.txt','r',encoding="UTF-8") as voornamenlijst:
    for line in voornamenlijst:
        line = re.sub("\r\n", "", line)
        columns = line.rstrip().split("\t")
        name = columns[0]
        freq = columns[-1]
        name = re.sub(" \([MV]\)","",name)
        if name in firstnames:
            firstnames[name] += int(freq)
        else:
            firstnames[name] = int(freq)

print("Read abbreviations list (capitalized words with length 2-4, frequency >= 50 in this data)")
abbreviations = dict()
with open('abbrev_freq.txt', 'r', encoding="UTF-8") as abbrevlist:
    for line in abbrevlist:
        line = re.sub("\r\n", "", line)
        columns = line.rstrip().split("\t")

        abbrev = columns[0]
        freq = columns[-1]
        if re.match("[0-9]",freq):
            if int(freq) >= 50:
                abbreviations[abbrev] = int(freq)

#for abbrev in abbreviations:
#    print (abbrev,abbreviations[abbrev])

print ("Read achternamenlijst")
lastnames = dict()
tree = ET.parse('familienamen_10kw.xml')
root = tree.getroot()
for record in root.iter('record'):
    if record is not None:
        name = record.find('naam')
        prefix = record.find('prefix')
        freq = record.find('n2007')

        if name.text is not None:
            achternaam = name.text
            if freq.text is not None:
                lastnames[achternaam] = int(freq.text)
                if prefix.text is not None:
                    #print (prefix.text, name.text)
                    achternaam = prefix.text+" "+name.text
                    lastnames[achternaam] = int(freq.text)

                    prefix_items = prefix.text.split(" ")
                    for item in prefix_items:
                        prefixes.add(item)

                #print (achternaam,lastnames[achternaam])

prefixes.add("der")
prefixes.add("vd")
prefixes.add("v")
prefixes.add("d")
prefixes.add("'t")
#print(prefixes)
#for achternaam in lastnames:
#    print (achternaam,lastnames[achternaam])

print ("Read CELEX frequencies")
celex_words = dict()
with open('DFW.CD','r',encoding="UTF-8") as celex:
    for line in celex:
        columns = line.rstrip().split('\\')
        word = columns[1]
        freq = int(columns[5])
        #print(word,freq)
        if word in celex_words:
            if freq > celex_words[word]:
                celex_words[word] = freq
        else:
            celex_words[word] = freq



def get_all_ngrams (text,maxn) :
    words = tokenize(text)

    i=0
    terms = dict()
    for word in words :
        if len(word) > 1 and '@' not in word:
            if word in terms :
                terms[word] += 1
            else :
                terms[word] = 1
        if len(words) >= 2 and maxn >= 2 :
            if i< len(words)-1 :
                #if words[i] not in stoplist and words[i+1] not in stoplist and words[i+1] != words[i]:
                if words[i+1] != words[i]:
                    bigram = str(words[i])+ " " +str(words[i+1])
                    if bigram in terms :
                        terms[bigram] += 1
                    else :
                        terms[bigram] = 1

                if len(words) >= 3 and maxn >= 3 :
                    if i < len(words)-2 :
                        if words[i+1] != words[i]:
                            trigram = str(words[i])+ " " +str(words[i+1])+ " " +str(words[i+2])
                            if trigram in terms :
                                terms[trigram] += 1
                            else :
                                terms[trigram] = 1
                    if len(words) >= 4 and maxn >= 4 :
                        if i < len(words)-3 :
                            if words[i+1] != words[i] and words[i+3] != words[i+2]:
                                fourgram = str(words[i])+ " " +str(words[i+1])+ " " +str(words[i+2])+ " " +str(words[i+3])
                                if fourgram in terms :
                                    terms[fourgram] += 1
                                else :
                                    terms[fourgram] = 1
                        if len(words) >= 4 and maxn >= 4 :
                            if i < len(words)-4 :
                                if words[i+1] != words[i] and words[i+3] != words[i+2] and words[i+4] != words[i+3]:
                                    fivegram = str(words[i])+ " " +str(words[i+1])+ " " +str(words[i+2])+ " " +str(words[i+3])+ " " +str(words[i+4])
                                    if fivegram in terms :
                                        terms[fivegram] += 1
                                    else :
                                        terms[fivegram] = 1
        i += 1
    return terms


def filter_ngrams(freq_dict):
    filtered_freq_dict = dict()
    for ngram in freq_dict:
        if re.match("^[a-zA-Z ,'.-]+$",ngram):
            filtered_freq_dict[ngram] = freq_dict[ngram]
    return filtered_freq_dict

def remove_overlapping_terms(terms):
    remove = set()

    for term1 in terms:
        for term2 in terms:
            if term1 != term2 and term1 in term2:
                #print ("remove",term1,"because we have",term2)
                remove.add(term1)

    selection = []

    for term in terms:
        if term not in remove:
            selection.append(term)
    return selection

def merge_partly_overlapping_terms(terms,item):
    columns_for_this_item = data_columns[str(item)] # json does not allow integers as keys, so it was stored with strings
    omschrijving = columns_for_this_item[3]

    terms_after_merging = []
    terms_merged = set()
    for term1 in terms:
        for term2 in terms:
            if term1 != term2 and omschrijving.index(term1) < omschrijving.index(term2):
                #words1 = term1.split(" ")
                longest_subterm = ""
                words2 = term2.split(" ")
                for i in range(0, len(words2) + 1):
                    for j in range(i + 1, len(words2) + 1):
                        subterm2 = " ".join(words2[i:j])
                        if subterm2 in term1:
                            if len(subterm2) > len(longest_subterm):
                                longest_subterm = subterm2

                if len(longest_subterm) > 0:
                    #print(term2, "partly overlaps with", term1, "(overlap:", longest_subterm, ")")
                    term2_tail = re.sub(longest_subterm,"",term2)
                    merged = term1+term2_tail
                    #print("MERGED",merged)
                    terms_after_merging.append(merged)
                    terms_merged.add(term1)
                    terms_merged.add(term2)
                    #print("REMOVE:",term1)
                    #print("REMOVE:",term2)
    for term in terms:
        if term not in terms_merged:
            terms_after_merging.append(term)

    return terms_after_merging

def potential_lastname(word):
    if word not in abbreviations \
            and word.lower() not in months \
            and not re.match(".*\.", word) \
            and re.match("^[A-Z].*", word) \
            and word.lower() not in celex_words \
            and not "Pdirekt" in word \
            and not re.match("[A-Za-z]+kosten", word):
        return True



initial = "^[A-Z]\.?$"
aanhef = "^(dhr|mevr|dr|drs|mr|mw|ir|ing|mrs|sr)\.?$"

def count_name_features(ngram):
    global initial
    global aanhef
    namefeats = []
    namescore = 0.0
    words = ngram.split(" ")
    #print (">",ngram)
    feats_per_index = dict()
    for i in range(0,len(words)+1):
        for j in range (i+1,len(words)+1):
            #if len(words) > i+j-2:
            subterm = " ".join(words[i:j])
            #print (">",subterm)
            if subterm.title() in firstnames:
                namefeats.append("firstname")
                # print(subterm,"firstname")
                for k in range(i, j):
                    feats_per_index[k] = "firstname"
            elif re.sub(",","",subterm).title() in lastnames or (" " in subterm and re.sub(",","",subterm) in lastnames):
                # gaat goed: Jong, P. de; W.DE RIJKE
                # fp: boek
                namefeats.append("lastname")
                #print(subterm, "lastname")
                for k in range(i,j):
                    feats_per_index[k] = "lastname"
            elif re.sub("\.$","",subterm.lower()) in prefixes:
                namefeats.append("prefix")
                #print(subterm,"prefix")
                for k in range(i,j):
                    feats_per_index[k] = "prefix"
            elif re.match(initial,subterm):
                namefeats.append("initial")
                #print(subterm,"initial")
                for k in range(i,j):
                    feats_per_index[k] = "initial"
            elif re.match(aanhef,subterm,re.IGNORECASE):
                #namefeats.append("aanhef")
                #print(subterm,"aanhef")
                for k in range(i,j):
                    feats_per_index[k] = "aanhef"
            elif re.match("^[A-Z][A-Z][A-Z]?$",subterm) and subterm not in abbreviations:
                namefeats.append("initials")
                #print(subterm,"initial")
                for k in range(i,j):
                    feats_per_index[k] = "initials"
            elif " " not in subterm and re.match("[A-Z][a-z].+",subterm)\
                    and subterm.upper() not in abbreviations \
                    and subterm.lower() not in months  \
                    and not re.match(".*\.",subterm) and subterm.lower() not in celex_words \
                    and not "Pdirekt" in subterm \
                    and not re.match("[A-Za-z]+kosten", subterm):


                namefeats.append("non-word")
                for k in range(i,j):
                    feats_per_index[k] = "non-word"


    if len(feats_per_index) == len(words)-1 and len(feats_per_index) == 1:
        for k in feats_per_index:
            if feats_per_index[k]== 'initial' or feats_per_index[k]== 'firstname':
                if len(words) >= k+2:
                    if potential_lastname(words[k+1]):
                        feats_per_index[k+1] = 'lastname?'
                        break
                elif k> 0 and k-1 not in feats_per_index:
                    if potential_lastname(words[k-1]):
                        feats_per_index[k-1] = 'lastname?'
                        break


    #print (words,feats_per_index)


    if len(feats_per_index) == len(words) and len(ngram) > 3:
        prefix_and_aanhef_only = True
        for k in feats_per_index:
            if feats_per_index[k] != 'prefix' and feats_per_index[k] != 'initial' and feats_per_index[k] != 'aanhef':
                prefix_and_aanhef_only = False
                # print ("Prefix and aanhef only:",ngram)
        if not prefix_and_aanhef_only:
            #print ("NAME:",ngram)
            namescore += len(namefeats)

    return namefeats, namescore






'''
MAIN
'''

ngram_counts = dict()
inverted_index =dict()
data_columns=dict()

num_lines = 0
for line in open(datafilename,'r',encoding="UTF-8"):
    num_lines += 1
    if num_lines > 10002:
        break

if num_lines > 10000 and os.path.isfile(json_ngrams_filename) and os.path.isfile(json_inverted_index) and os.path.isfile(json_data_columns):
    print(json_ngrams_filename,"already exists: read from json")
    with open(json_ngrams_filename,'r',encoding="UTF-8") as jsonfile:
        ngram_counts = json.load(jsonfile)
    print(json_inverted_index,"already exists: read from json")
    with open(json_inverted_index,'r',encoding="UTF-8") as jsonfile:
        inverted_index = json.load(jsonfile)
    print(json_data_columns,"already exists: read from json")
    with open(json_data_columns,'r',encoding="UTF-8") as jsonfile:
        data_columns = json.load(jsonfile)

else:
    print("Read", datafilename, ", read omschrijvingen into ngram dictionary, and save ngrams in inverted index")

    i=0
    with open(datafilename,'r',encoding='UTF-8') as data:
        for line in data:

            if i%1000 == 0:
                sys.stderr.write(str(i)+" ")
                sys.stderr.flush()
            if i%10000 == 0:
                sys.stderr.write('\n')
            if i>=no_of_lines_read:
                break

            #MINISTERIE, BOEKJAAR, NAAM LEVERANCIER, OMSCHRIJVING, BEDRAG, VALUTA, GB_DATUM, EUR_BEDRAG,
            line = re.sub("\r\n","",line)
            #print(line)
            if i > 0:
                columns = line.rstrip().split("\t")
                omschrijving = columns[3]

                data_columns[str(i)] = columns # json does not allow integer keys, so store as string
                ngrams = get_all_ngrams(omschrijving,maxn)
                #print (i,omschrijving,ngrams)
                ngrams = filter_ngrams(ngrams)
                for ngram in ngrams:
                    if ngram in ngram_counts:
                        ngram_counts[ngram] += ngrams[ngram]
                    else:
                        ngram_counts[ngram] = ngrams[ngram]
                    items_for_this_ngram = []
                    if ngram in inverted_index:
                        items_for_this_ngram = inverted_index[ngram]
                    items_for_this_ngram.append(i)
                    inverted_index[ngram] = items_for_this_ngram
            i +=1

    with open (json_ngrams_filename,'w',encoding="UTF-8") as jsonfile:
        json.dump(ngram_counts,jsonfile)

    with open (json_inverted_index,'w',encoding="UTF-8") as jsonfile:
        json.dump(inverted_index,jsonfile)

    with open (json_data_columns,'w',encoding="UTF-8") as jsonfile:
        json.dump(data_columns,jsonfile)




print("Count name evidence for",len(ngram_counts),"ngrams and store names per item")

names_per_item = dict()
all_names_uniq = dict() #key is name, value is evidence and score information
j = 0
for ngram in inverted_index:
    if j % 10000 == 0:
        sys.stderr.write(str(j) + " ")
        sys.stderr.flush()
    if j % 100000 == 0:
        sys.stderr.write('\n')
    j += 1


    name_features, name_score = count_name_features(ngram)


    jointevidence = "+".join(name_features)
    #print(ngram,name_score)
    if name_score >= 1.0:

        items_for_this_ngram = inverted_index[ngram]

        for item in items_for_this_ngram:
            names_for_this_item = []
            if item in names_per_item:
                names_for_this_item = names_per_item[item]
            names_for_this_item.append(ngram) # add this ngram to the array of names for this item
            names_per_item[item] = names_for_this_item

for item in names_per_item:
    #print ("#",item,": names for this item:",names_for_this_item)
    names_without_overlap = remove_overlapping_terms(names_per_item[item])
    names_merged = merge_partly_overlapping_terms(names_without_overlap,item)
    names_per_item[item] = names_merged



print("Print items with names")
records_with_names_file = open(records_with_names_filename,'w',encoding="UTF-8")
records_with_names_file.write("id\tomschrijving anoniem\tnames (automatic)\tnames (manual)\n")


item_count = 0
count_no_names = 0
name_count = 0

for item in data_columns:
    #print ("item:",item)
    item_count +=1
    columns_for_this_item = data_columns[str(item)] # json does not allow integers as keys, so it was stored with strings
    omschrijving = columns_for_this_item[3]
    omschrijving_anonymized = omschrijving

    has_name = False

    if int(item) in names_per_item:

        for name in names_per_item[int(item)]:
            #print (omschrijving,name)
            omschrijving_anonymized = re.sub(name,"***",omschrijving_anonymized)

            has_name = True
            name_count += 1

        records_with_names_file.write(str(item) + "\t" + omschrijving_anonymized + "\t" + str(names_per_item[int(item)])+"\n")



    if not has_name:
        records_with_names_file.write(str(item) + "\t" + omschrijving_anonymized+"\n")
        count_no_names +=1



records_with_names_file.close()

print("total number of rows in the data:",item_count-1)
print("number of rows with at least one name:",item_count-count_no_names)
print("number of names found:",name_count)
