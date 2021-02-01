#!/usr/bin/env python3
# coding: utf-8

# Contains functions for lemmatizing text


from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from gensim import models
import numpy as np
import pandas as pd
import string
import re


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

def drop_nonalpha(df):
	alpha_pattern = r'[a-zA-Z]'
	regex_pat = re.compile(alpha_pattern, flags=re.IGNORECASE)
	df['has_alpha'] = df['text_clean'].str.contains(regex_pat)
	df.loc[~df['has_alpha'], 'text_clean'] = ""
	df['text_clean'].replace('', np.nan, inplace=True)
	df.dropna(subset=['text_clean'], inplace=True)
	df.drop('has_alpha', axis=1, inplace=True)
	return df

def make_bigrams(text):
	bigram = models.Phrases(text, min_count=5)
	bigram_mod = models.phrases.Phraser(bigram)
	return [bigram_mod[t] for t in text]

def clean_data(df):
	df = replace_email(df)
	df = replace_lonely_numbers(df)
	df = drop_nonalpha(df)
	text = df['text_clean'].apply(clean_text)
	tokenizer = RegexpTokenizer(r'\w+')
	text = text.apply(tokenizer.tokenize)
	text = text.apply(remove_stopwords)
	text = text.apply(lemmatize)
	text = text.tolist()
	text_bigrams = make_bigrams(text)
	return text_bigrams

def gen_sql(subforum="special-needs", group="parent"):
	if group=="parent":
		sql = '''
			SELECT t.message_id AS message_id, t.text_clean AS text_clean
			FROM text AS t
			JOIN posts AS p
			ON t.message_id = p.message_id
			WHERE p.subforum="{}" AND p.parent_id="" AND t.text_clean<>"" AND t.probable_spam=0
		'''
	elif group=="all":
		sql = '''
			SELECT t.message_id AS message_id, t.text_clean AS text_clean
			FROM text AS t
			JOIN posts AS p
			ON t.message_id = p.message_id
			WHERE p.subforum="{}" AND t.text_clean<>"" AND t.probable_spam=0
		'''
	elif group=="child":
		sql = '''
			SELECT t.message_id AS message_id, t.text_clean AS text_clean
			FROM text AS t
			JOIN posts AS p
			ON t.message_id = p.message_id
			WHERE p.subforum="{}" AND p.parent_id<>"" AND t.text_clean<>"" AND t.probable_spam=0
		'''
	return sql.format(subforum)

def gen_sql_dates(subforum="special-needs", group="parent"):
	if group=="parent":
		sql = '''
			SELECT t.message_id AS message_id, t.text_clean AS text_clean, p.date_created AS date_created
			FROM text AS t
			JOIN posts AS p
			ON t.message_id = p.message_id
			WHERE p.subforum="{}" AND p.parent_id="" AND t.text_clean<>"" AND t.probable_spam=0
		'''
	elif group=="all":
		sql = '''
			SELECT t.message_id AS message_id, t.text_clean AS text_clean, p.date_created AS date_created
			FROM text AS t
			JOIN posts AS p
			ON t.message_id = p.message_id
			WHERE p.subforum="{}" AND t.text_clean<>"" AND t.probable_spam=0
		'''
	elif group=="child":
		sql = '''
			SELECT t.message_id AS message_id, t.text_clean AS text_clean, p.date_created AS date_created
			FROM text AS t
			JOIN posts AS p
			ON t.message_id = p.message_id
			WHERE p.subforum="{}" AND p.parent_id<>"" AND t.text_clean<>"" AND t.probable_spam=0
		'''
	return sql.format(subforum)