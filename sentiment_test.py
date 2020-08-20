# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 19:34:54 2020

@author: mwhuhn
"""

# Imports

import sqlite3
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from scipy.stats import ttest_ind
from datetime import datetime
from nltk.probability import FreqDist
from nltk.tokenize import RegexpTokenizer, word_tokenize
from nltk.corpus import stopwords
import string
import re

# Functions

def format_data(df):
    df['date_recorded'] = pd.to_datetime(df['date_recorded'])
    df['date_created'] = pd.to_datetime(df['date_created'])
    # text = title + body
    df['title'] = df['title'].replace('This post has been deleted\.', '', regex=True)
    df['text'] = df['title'] + " " + df['body']
    return df

def sentiment_analyzer_scores(sentence, analyzer):
    score = analyzer.polarity_scores(sentence)
    return score

def ttest_sentiment(df, v):
    group_before = df.where(df['date_created'] < datetime(2020, 2, 28, 0, 0, 0))[v].dropna()
    group_after = df.where(df['date_created'] > datetime(2020, 4, 1, 0, 0, 0))[v].dropna()
    print("Mean before: " + str(group_before.mean()))
    print("Mean after: " + str(group_after.mean()))
    return ttest_ind(group_before, group_after, equal_var=False, nan_policy="omit")

def clean_text(text):
    clean = "".join([t for t in text if t not in string.punctuation])
    clean = re.sub(" +", " ", clean)
    clean = clean.strip()
    clean = clean.lower()
    return clean

def remove_stopwords(text):
    words = [w for w in text if w not in stopwords.words('english')]
    return words

def main():
    db_file = "./database/rawCrawl.db"
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * from Youbemom_raw", conn)
    df = format_data(df)
    analyzer = SentimentIntensityAnalyzer()
    sentiment = df['text'].apply(lambda x: sentiment_analyzer_scores(x, analyzer))
    df['neg_sentiment'] = sentiment.apply(lambda x: x.get('neg', 0))
    df['neu_sentiment'] = sentiment.apply(lambda x: x.get('neu', 0))
    df['pos_sentiment'] = sentiment.apply(lambda x: x.get('pos', 0))
    df['compound_sentiment'] = sentiment.apply(lambda x: x.get('compound', 0))
    ttest_sentiment(df, 'neg_sentiment')
    ttest_sentiment(df, 'neu_sentiment')
    ttest_sentiment(df, 'pos_sentiment')
    ttest_sentiment(df, 'compound_sentiment')
    text = df['text']
    text = text.apply(clean_text)
    tokenizer = RegexpTokenizer(r'\w+')
    text = text.apply(tokenizer.tokenize)
    text = text.apply(remove_stopwords)
    joined_text = text.apply(lambda x: " ".join(x))
    sentiment_clean = joined_text.apply(lambda x: sentiment_analyzer_scores(x, analyzer))
    df['neg_sentiment_clean'] = sentiment_clean.apply(lambda x: x.get('neg', 0))
    df['neu_sentiment_clean'] = sentiment_clean.apply(lambda x: x.get('neu', 0))
    df['pos_sentiment_clean'] = sentiment_clean.apply(lambda x: x.get('pos', 0))
    df['compound_sentiment_clean'] = sentiment_clean.apply(lambda x: x.get('compound', 0))
    ttest_sentiment(df, 'neg_sentiment_clean')
    ttest_sentiment(df, 'neu_sentiment_clean')
    ttest_sentiment(df, 'pos_sentiment_clean')
    ttest_sentiment(df, 'compound_sentiment_clean')
    # fdist = FreqDist(joined_text)
    # fdist.most_common(50)

# Main
if __name__ == '__main__':
    main()