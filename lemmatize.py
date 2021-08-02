#!/usr/bin/env python3
# coding: utf-8

# Contains functions for lemmatizing text

# nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
# gensim
from gensim import corpora, models
# data
import numpy as np
import pandas as pd
import string
import re
import emoji
import random
# paths
from pathlib import Path
from io import FileIO
# db
import sqlite3
from scraping import create_connection
# saving
import pickle

## File Locations

p = Path.cwd()
path_parent = p.parents[0]

path_db = str(path_parent / "database" / "youbemom-merged.db")
path_clean_data = path_parent / "clean_data"
path_lemma_pkl = str(path_clean_data / "lemmatized_text_{0}_{1}_{2}.pkl")
path_corpus_pkl = str(path_clean_data / "corpus_{0}_{1}_{2}.pkl")
path_dictionary_gensim = str(path_clean_data / "dictionary_{0}_{1}_{2}.gensim")
path_clean_text = str(path_clean_data / "clean_text_{0}_{1}.csv")

## Regex

emoticon_lookaround = r'(?:(^)|(\s)|(?<=:\-\))|(?<=:\))|(?<=:\-\])|(?<=:\]:\-3)|(?<=:3)|(?<=:\->)|(?<=:>)|(?<=8\-\))|(?<=8\))|(?<=:\-\}})|(?<=:\}})|(?<=:o\))|(?<=:c\))|(?<=:\^\))|(?<==\])|(?<==\))|(?<=:\-D)|(?<=:D)|(?<=8\-D)|(?<=8D)|(?<=x\-D)|(?<=xD)|(?<=X\-D)|(?<=XD)|(?<==D)|(?<==3)|(?<=B\^D)|(?<=c:)|(?<=C:)|(?<=:\-\()|(?<=:\()|(?<=:\-c)|(?<=:c)|(?<=:\-<)|(?<=:<)|(?<=:\-\[)|(?<=:\[)|(?<=:\-\|\|)|(?<=>:\[)|(?<=:\{{)|(?<=:@)|(?<=:\()|(?<=;\()|(?<=:\'\-\()|(?<=:\'\()|(?<=:\'\-\))|(?<=:\'\))|(?<=D\-\':)|(?<=D:<)|(?<=D:)|(?<=D8)|(?<=D;)|(?<=D=)|(?<=DX)|(?<=:\-O)|(?<=:O)|(?<=:\-o)|(?<=:o)|(?<=:\-0)|(?<=8\-0)|(?<=>:O)|(?<=O_O)|(?<=o-o)|(?<=O_o)|(?<=o_O)|(?<=o_o)|(?<=O-O)|(?<=:\-\*)|(?<=:\*)|(?<=:x)|(?<=;\-\))|(?<=;\))|(?<=\*\-\))|(?<=\*\))|(?<=;\-\])|(?<=;\])|(?<=;\^\))|(?<=:\-,)|(?<=;D)|(?<=:\-P)|(?<=:P)|(?<=X\-P)|(?<=XP)|(?<=x\-p)|(?<=xp)|(?<=:\-p)|(?<=:p)|(?<=:\-Þ)|(?<=:Þ)|(?<=:\-þ)|(?<=:þ)|(?<=:\-b)|(?<=:b)|(?<=d:)|(?<==p)|(?<=>:P)|(?<=:\-/)|(?<=:/)|(?<=:\-\.)|(?<=>:\\)|(?<=>:/)|(?<=:\\)|(?<==/)|(?<==\\)|(?<=:L)|(?<==L)|(?<=:S)|(?<=:\-\|)|(?<=:\|)|(?<=<3)|(?<=<\\3)|(?<=\\[oO]/)){}(?=($|\s|:\-\)|:\)|:\-\]|:\]:\-3|:3|:\->|:>|8\-\)|8\)|:\-\}}|:\}}|:o\)|:c\)|:\^\)|=\]|=\)|:\-D|:D|8\-D|8D|x\-D|xD|X\-D|XD|=D|=3|B\^D|c:|C:|:\-\(|:\(|:\-c|:c|:\-<|:<|:\-\[|:\[|:\-\|\||>:\[|:\{{|:@|:\(|;\(|:\'\-\(|:\'\(|:\'\-\)|:\'\)|D\-\':|D:<|D:|D8|D;|D=|DX|:\-O|:O|:\-o|:o|:\-0|8\-0|>:O|O_O|o-o|O_o|o_O|o_o|O-O|:\-\*|:\*|:x|;\-\)|;\)|\*\-\)|\*\)|;\-\]|;\]|;\^\)|:\-,|;D|:\-P|:P|X\-P|XP|x\-p|xp|:\-p|:p|:\-Þ|:Þ|:\-þ|:þ|:\-b|:b|d:|=p|>:P|:\-/|:/|:\-\.|>:\\|>:/|:\\|=/|=\\|:L|=L|:S|:\-\||:\||<3|<\\3|\\[oO]/))'

## Functions

def save_clean_text(df, subforum="all", group="all"):
	df.to_csv(path_clean_text.format(subforum, group), index=False)

def process_data(subforum="all", group="all", id_type="family_id", per=1, n_chunks=1):
	if Path(path_clean_text.format(subforum, group)).exists():
		df = pd.read_csv(path_clean_text.format(subforum, group))
		print("found clean text")
	else:
		print("creating new clean text")
		df = load_data(subforum, group, per)
		df = clean_data(df)
		save_clean_text(df, subforum, group)
		print("saved clean text")
	print("text to list")
	df['bigrams'] = text_to_list(df['text_clean'], n_chunks)
	if id_type == "family_id":
		print("making bigrams")
		df['bigrams'] = make_bigrams(df['bigrams'], n_chunks)
		print("grouping by family_id")
		text = df[['family_id','bigrams']].groupby(['family_id'])['bigrams'].sum().tolist()
	else:
		print("making bigrams")
		text = make_bigrams(df['bigrams'], n_chunks)
	print("saving data")
	save_data(text, subforum, group, id_type, n_chunks)

def load_data(subforum="all", group="all", per=1):
	conn = create_connection(path_db)
	if subforum == "school": # never percent sample
		sql = gen_sql_school(group)
	elif per == 1: # only for toddler
		sql = gen_sql(subforum, group)
	else:
		sql_temp = gen_samp_sql_per(subforum)
		temp = pd.read_sql_query(sql_temp, conn)
		temp = temp.sample(frac=per, random_state=232)
		temp.to_sql('temp', conn, if_exists='replace', index=False)
		sql = gen_sql_per(group)
	df = pd.read_sql_query(sql, conn)
	conn.close()
	return df

def save_data(text, subforum="all", group="all", id_type="family_id", n_chunks=1):
	pickle.dump(text, open(path_lemma_pkl.format(subforum, group, id_type), 'wb'))
	dictionary = corpora.Dictionary(text)
	dictionary.save(FileIO(path_dictionary_gensim.format(subforum, group, id_type), "wb"))
	if n_chunks > 1:
		length = len(text)
		size = length // n_chunks + (length % n_chunks > 0) # round up
		corpus = []
		for grp in chunk_list(text, size): # iterable
			corpus = corpus + [dictionary.doc2bow(g) for g in grp]
	else:
		corpus = [dictionary.doc2bow(t) for t in text]
	pickle.dump(corpus, open(path_corpus_pkl.format(subforum, group, id_type), 'wb'))

def chunk_list(l, n):
	"""Yield successive n-sized chunks from lst."""
	for i in range(0, len(l), n):
		yield l[i:i + n]

def clean_text(text):
	""" cleans the input text of punctuation, extra
		spaces, and makes letters lower case
	:param text: text (= title + body here)
	:return clean: clean text
	"""
	try:
		clean = "".join([t for t in text if t not in string.punctuation])
	except:
		print(text)
	clean = re.sub(" +", " ", clean)
	clean = clean.strip()
	clean = clean.lower()
	return clean

def remove_stopwords(text):
	""" remove all stop words from the text
		using stopwords from nltk.corpus
	:param text: text with stopwords
	:return words: text without stopwords
	"""
	words = [w for w in text if w not in stopwords.words('english')]
	return words

def encode_utf8(text):
	words = [w.encode() for w in text]
	return words

def get_lemma(word):
	lemma = wn.morphy(word)
	if lemma is None:
		return word
	else:
		return lemma

def lemmatize(text):
	lemmas = [get_lemma(w) for w in text]
	return lemmas

def replace_lonely_numbers(df):
	lonely_number_pattern = r'^[0-9]+$'
	regex_pat = re.compile(lonely_number_pattern, flags=re.IGNORECASE)
	df['text_clean'] = df['text_clean'].str.replace(regex_pat, "")
	df['text_clean'] = df['text_clean'].str.strip()
	return df

def replace_email(df):
	email_pattern = r'([-a-zA-Z0-9_\.\+]+@[-a-zA-Z0-9]+\.[-a-zA-Z0-9\.]+)'
	regex_pat = re.compile(email_pattern, flags=re.IGNORECASE)
	df['text_clean'] = df['text_clean'].str.replace(regex_pat, "")
	df['text_clean'] = df['text_clean'].str.strip()
	return df

def replace_emoji(df):
	# See: https://en.wikipedia.org/wiki/List_of_emoticons
	emoticons = [
		[r'(:\-\)|:\)|:\-\]|:\]:\-3|:3|:\->|:>|8\-\)|8\)|:\-\}|:\}|:o\)|:c\)|:\^\)|=\]|=\))',' emojismile '],
		[r'(:\-D|:D|8\-D|8D|x\-D|xD|X\-D|XD|=D|=3|B^D|c:|C:)',' emojilaughing '],
		[r'(:\-\(|:\(|:\-c|:c|:\-<|:<|:\-\[|:\[|:\-\|\||>:\[|:\{|:@|:\(|;\()',' emojifrowning '],
		[r'(:\'\-\(|:\'\()',' emojicry '],
		[r'(:\'\-\)|:\'\))',' emojijoy '],
		[r'(D\-\':|D:<|D:|D8|D;|D=|DX)',' emojianguished '],
		[r'(:\-O|:O|:\-o|:o|:\-0|8\-0|>:O|O_O|o-o|O_o|o_O|o_o|O-O)',' emojiopenmouth '],
		[r'(:\-\*|:\*|:x)',' emojikissing '],
		[r'(;\-\)|;\)|\*\-\)|\*\)|;\-\]|;\]|;\^\)|:\-,|;D)',' emojiwink '],
		[r'(:\-P|:P|X\-P|XP|x\-p|xp|:\-p|:p|:\-Þ|:Þ|:\-þ|:þ|:\-b|:b|d:|=p|>:P)',' emojistuckouttongue '],
		[r'(:\-/|:/|:\-\.|>:\\|>:/|:\\|=/|=\\|:L|=L|:S)',' emojiconfused '],
		[r'(:\-\||:\|)',' emojiexpressionless '],
		[r'(<3)',' emojiheart '],
		[r'(<\\3)',' emojibrokenheart '],
		[r'(\\[oO]/)',' emojicheer ']
	]
	for grp in emoticons:
		pattern = emoticon_lookaround.format(grp[0])
		df['text_clean'] = df['text_clean'].str.replace(re.compile(pattern), grp[1])
	df['text_clean'] = df['text_clean'].apply(lambda x: emoji.demojize(x, delimiters=(" emoji", " ")))
	return df

def drop_nonalpha(df):
	alpha_pattern = r'[a-zA-Z]'
	regex_pat = re.compile(alpha_pattern, flags=re.IGNORECASE)
	df['has_alpha'] = df['text_clean'].str.contains(regex_pat)
	df.loc[~df['has_alpha'], 'text_clean'] = ""
	df['text_clean'].replace('', np.nan, inplace=True)
	df.dropna(subset=['text_clean'], inplace=True)
	df.drop('has_alpha', axis=1, inplace=True)
	return df

def make_bigrams(text, n_chunks=1):
	bigram = models.Phrases(text, min_count=5)
	bigram_mod = models.phrases.Phraser(bigram)
	result = []
	for grp in np.array_split(text, n_chunks):
		grp = grp.tolist()
		result = result + [bigram_mod[g] for g in grp]
	return result

def clean_data(df):
	df = replace_emoji(df)
	df = replace_email(df)
	df = replace_lonely_numbers(df)
	df = drop_nonalpha(df)
	df['text_clean'] = df['text_clean'].apply(clean_text)
	return df

def text_to_list(text, n_chunks=1):
	tokenizer = RegexpTokenizer(r'\w+')
	result = []
	for grp in np.array_split(text, n_chunks):
		grp = grp.apply(tokenizer.tokenize)
		grp = grp.apply(remove_stopwords)
		grp = grp.apply(lemmatize)
		grp = grp.tolist()
		result = result + grp
	return result

def gen_sql(subforum="all", group="all"):
	sql = '''SELECT p.family_id AS family_id, t.message_id AS message_id, t.text_clean AS text_clean
		FROM text AS t
		JOIN posts AS p
		ON t.message_id = p.message_id
		WHERE'''
	if subforum != "all":
		sql = sql + ''' p.subforum="{}" AND'''.format(subforum)
	if group=="parent":
		sql = sql + ''' p.parent_id="" AND'''
	elif group=="child":
		sql = sql + ''' p.parent_id="<>" AND'''
	sql = sql + ''' t.text_clean<>"" AND t.probable_spam=0'''
	return sql

def gen_sql_dates(subforum="all", group="all"):
	sql = '''SELECT p.family_id AS family_id, t.message_id AS message_id, t.text_clean AS text_clean, p.date_created AS date_created
		FROM text AS t
		JOIN posts AS p
		ON t.message_id = p.message_id
		WHERE'''
	if subforum != "all":
		sql = sql + ''' p.subforum="{}" AND'''.format(subforum)
	if group=="parent":
		sql = sql + ''' p.parent_id="" AND'''
	elif group=="child":
		sql = sql + ''' p.parent_id="<>" AND'''
	sql = sql + ''' t.text_clean<>"" AND t.probable_spam=0'''
	return sql

def gen_samp_sql_per(subforum="all"):
	if subforum=="all":
		return ''' SELECT family_id FROM threads '''
	else:
		return ''' SELECT family_id FROM threads WHERE subforum="{}" '''.format(subforum)

def gen_sql_per(group="all"):
	sql = '''SELECT p.family_id AS family_id, t.message_id AS message_id, t.text_clean AS text_clean
		FROM text AS t
		JOIN posts AS p
		ON t.message_id = p.message_id
		WHERE p.family_id IN (SELECT family_id FROM temp) AND'''
	if group=="parent":
		sql = sql + ''' p.parent_id="" AND'''
	elif group=="child":
		sql = sql + ''' p.parent_id="<>" AND'''
	sql = sql + ''' t.text_clean<>"" AND t.probable_spam=0'''
	return sql

def gen_sql_school(group="all"):
	sql = '''SELECT p.family_id AS family_id, t.message_id AS message_id, t.text_clean AS text_clean
		FROM text AS t
		JOIN posts AS p
		ON t.message_id = p.message_id
		WHERE (p.subforum="tween-teen" OR p.subforum="elementary" OR p.subforum="preschool") AND'''
	if group=="parent":
		sql = sql + ''' p.parent_id="" AND'''
	elif group=="child":
		sql = sql + ''' p.parent_id="<>" AND'''
	sql = sql + ''' t.text_clean<>"" AND t.probable_spam=0'''
	return sql
