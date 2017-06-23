import numpy as np
import pandas as pd
import nltk
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
import enchant

nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')


def tag2pos(tag, returnNone=False):
    ap_tag = {'NN': wn.NOUN, 'JJ': wn.ADJ,
              'VB': wn.VERB, 'RB': wn.ADV}
    try:
        return ap_tag[tag[:2]]
    except:
        return None if returnNone else ''


def lemmatize_df(df):
    # lemmatize speech acts
    for index, row in df.iterrows():
        # initialize lemma list
        lemma_list = []
        # tokenize word_pos
        if type(row['SPEECH_ACT']) == str:
            tokens = word_tokenize(row['SPEECH_ACT'])
            alpha_tokens = [token for token in tokens if token.isalpha()]
            spellchecked_tokens = [token for token in alpha_tokens
                                   if dictionary.check(token)]
            tagged_tokens = pos_tag(spellchecked_tokens)
            for tagged_token in tagged_tokens:
                word = str(tagged_token[0])
                word_pos = tagged_token[1]
                word_pos_morphed = tag2pos(word_pos)
                if word_pos_morphed is not '':
                    lemma = lemmatizer.lemmatize(word, word_pos_morphed)
                else:
                    lemma = lemmatizer.lemmatize(word)
                lemma_list.append(lemma)
            lemma_string = ' '.join(lemma_list)
            df.loc[index, 'LEMMAS'] = lemma_string
        else:
            print str(index) + "Not string"
            df.loc[index, 'SPEECH_ACT'] = 'not string'
            df.loc[index, 'LEMMAS'] = 'not string'
            continue

    return(df)


# load British English spell checker
dictionary = enchant.Dict("en_GB")
# lemmatizer
lemmatizer = WordNetLemmatizer()
word = ['Germans']
word2 = ['apple']
word_pos = pos_tag(word)[0][1]
word_pos_morphed = tag2pos(word_pos)
word_pos2 = pos_tag(word2)[0][1]
word_pos_morphed2 = tag2pos(word_pos2)
lemmatizer.lemmatize(str(word), word_pos_morphed)
lemmatizer.lemmatize(str(word2), word_pos_morphed2)
lemmatizer.lemmatize('Germany', 'n')
lemmatizer.lemmatize('Germanic', 'a')
lemmatizer.lemmatize('German', 'n')
lemmatizer.lemmatize('Germans')
lemmatizer.lemmatize('apple')
lemmatizer.lemmatize('apples')
lemmatizer.lemmatize('bicycle')
lemmatizer.lemmatize('bicycles')
lemmatizer.lemmatize('bikes')
lemmatizer.lemmatize('bicycling')

from nltk.stem.porter import *
stemmer = PorterStemmer()
stemmer.stem('German')
stemmer.stem('Germans')
stemmer.stem('Germanic')
stemmer.stem('Germany')
stemmer.stem('bicycle')
stemmer.stem('bicycle')
stemmer.stem('bikes')
stemmer.stem('bicycling')

path_output = '/users/alee35/scratch/land-wars-devel-data/'
path = '/gpfs/data/datasci/paper-m/HANSARD/speeches_dates/'
path_seed = '/gpfs/data/datasci/paper-m/free_seed/seed_segmented/'

# create as many processes as there are CPUs on your machine
#num_processes = multiprocessing.cpu_count()
# calculate the chunk size as an integer
#chunk_size = int(text.shape[0]/num_processes)
# works even if the df length is not evenly divisible by num_processes
#chunks = [text.ix[text.index[i:i + chunk_size]]
#          for i in range(0, text.shape[0], chunk_size)]
# create our pool with `num_processes` processes
#pool = multiprocessing.Pool(processes=num_processes)
# apply our function to each chunk in the list
#result = pool.map(lemmatize_df, chunks)
# combine the results from our pool to a dataframe
#textlem = pd.DataFrame().reindex_like(text)
#textlem['LEMMAS'] = np.NaN
#for i in range(len(result)):
#    textlem.ix[result[i].index] = result[i]


with open(path + 'membercontributions-20161026.tsv', 'r') as f:
    text = pd.read_csv(f, sep='\t')

# get year from date
text['YEAR'] = text.DATE.str[:4]
# convert years column to numeric
text['YEAR'] = text['YEAR'].astype(float)
# change years after 1908 to NaN
for index, row in text.iterrows():
    if row['YEAR'] > 1908:
        text.loc[index, 'YEAR'] = np.NaN
        # forward fill missing dates
        text['YEAR'] = text['YEAR'].fillna(method='ffill')
        # compute decade
        text['DECADE'] = (text['YEAR'].map(lambda x: int(x) - (int(x) % 10)))

text.drop(['ID', 'DATE', 'DECADE', 'MEMBER', 'CONSTITUENCY'], axis=1, inplace=True)

# convert integer speech acts to string
for index, row in text.iterrows():
    if type(row['SPEECH_ACT']) != str:
        text.loc[index, 'SPEECH_ACT'] = 'Not Text'

# groupby year, decade, bill, and concatenate speech act with a space
text = text.groupby(['BILL', 'YEAR'])['SPEECH_ACT'].agg(lambda x: ' '.join(x)).reset_index()

# append speech acts to text
with open(path_seed + 'four_corpus_and_other_cols.txt', 'r') as f:
    seed = pd.read_csv(f, sep='\t', header=None, names=['BILL','YEAR','SPEECH_ACT'])
text = pd.concat([text, seed]).reset_index(drop=True)

# lemmatize text
textlem = lemmatize_df(text)

textlem.to_csv(path_output + "cleanbills-20170517.tsv", sep="\t", header=True, index=False)
