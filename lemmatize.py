#!/usr/bin/env python3
# coding: utf-8

# Contains functions for lemmatizing text


from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import string
import re


def clean_text(text):
    """ cleans the input text of punctuation, extra
        spaces, and makes letters lower case
    :param text: text (= title + body here)
    :return clean: clean text
    """
    clean = "".join([t for t in text if t not in string.punctuation])
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

def clean_data(df):
    text = df['text_clean']
    text = text.apply(clean_text)
    tokenizer = RegexpTokenizer(r'\w+')
    text = text.apply(tokenizer.tokenize)
    text = text.apply(remove_stopwords)
    text = text.apply(lemmatize)
    return text