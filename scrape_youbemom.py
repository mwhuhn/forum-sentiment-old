# -*- coding: utf-8 -*-
"""
Created: Aug 06 2020
Edited:  Aug 17 2020

@author: mwhuhn

Scrapes the Youbemom Special Needs Forum
"""

# Imports ----

from time import sleep
import re
import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests


#    DB Structure
#    id: automatically assigned
#    url: url of top post
#    message_id: the unique id of the message from the html
#    date_recorded: date the data is fetched
#    date_created: date the data was created
#    title: title of the post
#    body: body of the post
#    family_group: by top post number
#    family_count: post number within family group using depth first search
#    parent_id: family_group of post this is responding to


# Functions ----

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as err:
        print(err)
    return conn

def set_up_db(conn):
    """ if the database exists, drop it and create a
        SQLite database for the results
    :param conn: database connection
    :return: nothing
    """
    cur = conn.cursor()
    cur.executescript('''
        DROP TABLE IF EXISTS Youbemom_raw;
        
        CREATE TABLE Youbemom_raw (
        	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        	url TEXT,
            message_id TEXT,
        	date_recorded TEXT,
        	date_created TEXT,
        	title TEXT,
        	body TEXT,
        	family_group INTEGER,
        	family_count INTEGER,
        	parent_id INTEGER
        );
    ''')

def get_soup(next_url):
    """ get the soup from the url
    :param next_url: string of next url to query
    :return: soup of url html
    """
    res_next = requests.get(next_url)
    soup = BeautifulSoup(res_next.content, "html.parser")
    return soup

def get_top_posts(soup):
    """ get each main list item from the page
    :param soup: url's html
    :return lis: list of list items (main topics of the
                 forum on the page)
    """
    ol = soup.find('ol', id="thread-list")
    lis = ol.find_all('li', recursive=False)
    return lis

def fix_ago(date_created, date_recorded):
    if "hr" in date_created:
        if "min" in date_created:
            l = re.findall("[0-9]+", date_created)
            dc = datetime.strptime(date_recorded, "%m-%d-%Y %H:%M:%S") - timedelta(hours=int(l[0]), minutes=int(l[1]))
        else:
            l = re.findall("[0-9]+", date_created)[0]
            dc = datetime.strptime(date_recorded, "%m-%d-%Y %H:%M:%S") - timedelta(hours=int(l))        
    else:
        l = re.findall("[0-9]+", date_created)[0]
        dc = datetime.strptime(date_recorded, "%m-%d-%Y %H:%M:%S") - timedelta(minutes=int(l))
    return dc.strftime("%m-%d-%Y %H:%M:%S")

def parse_top_post(li, conn, family_group, date_recorded):
    """ parse the list items into a format that can be
        inserted into the database
    :param li: input list item string
    :param conn: connection to db
    :param family_group: top post number
    :param date_recorded: date scraping the data
    :return parsed: a list of items to insert into db
    :note family_count is always 1 for top posts in family group
    """
    url = li.find("a", text=re.compile("permalink"))["href"]
    date_created = li.find('span', {'class' : 'meta date'}).get_text()
    # if doesn't contain "ago", change time with strptime
    if "ago" in date_created:
        date_created = fix_ago(date_created, date_recorded)
    else:
        date_created = datetime.strptime(date_created, "%m-%d-%Y %I:%M%p")
    title = li.find('span', {'class' : re.compile('noskimwords post')}).get_text()
    title = title.replace('...(more)', '')
    message_id = li.find('span', {'class' : re.compile('noskimwords post')})["id"]
    body = li.find('div', {'class' : 'message', 'id' : message_id}, recursive=False)
    if body:
        body_text = body.get_text()
        body_text = body_text.replace('log in or sign up to post a comment', '')
    else:
        body_text = ""
    parent_id = 0
    parsed = (url, message_id, date_recorded, date_created, title, body_text, family_group, 1, parent_id)
    write_to_db(parsed, conn)
    return date_created

def parse_next_level(li, conn, family_group, family_count, parent_id, date_recorded):
    """ parse the list items into a format that can be
        inserted into the database
    :param n: input next list item string
    :param conn: connection to db
    :param family_group: top post number
    :param parent: id of parent in list
    :param date_recorded: date scraping the data
    :return parsed: a list of items to insert into db
    :note: no URL for lower-level messages
    """
    date_created = li.find('span', {'class' : 'meta date'}).get_text()
    # if doesn't contain "ago", change time with strptime
    if "ago" in date_created:
        date_created = fix_ago(date_created, date_recorded)
    else:
        date_created = datetime.strptime(date_created, "%m-%d-%Y %I:%M%p")
    title = li.find('span', {'class' : re.compile('noskimwords reply')}).get_text()
    title = title.replace('...(more)', '')
    message_id = li.find('span', {'class' : re.compile('noskimwords reply')})["id"]
    body = li.find('div', {'class' : 'message', 'id' : "p" + message_id}, recursive=False)
    if body:
        body_text = body.get_text()
        body_text = body_text.replace('log in or sign up to post a comment', '')
    else:
        body_text = ""
    parsed = ('', message_id, date_recorded, date_created, title, body_text, family_group, family_count, parent_id)
    write_to_db(parsed, conn)

def write_to_db(parsed, conn):
    """ inserts the parsed data into the database
    :param parsed: a tuple of the parsed data
    :return: nothing
    """
    sql = ''' INSERT INTO Youbemom_raw(url,message_id,date_recorded,date_created,title,body,family_group,family_count,parent_id)
    VALUES(?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, parsed)
    conn.commit()

def get_next_level(next_level, conn, family_group, family_count, parent_id, date_recorded):
    """ recursively gets the next lower level of the forum posts
    :param next_level: the next level of the post, checks for a lower one
    :param conn: db connection to insert data
    :param family_group: the top-level family group for this post
    :param family_count: post number within the family (depth first search)
    :param parent_id: the count of the parent post
    :param date_recorded: the date this is being recorded
    :return: nothing
    """
    for nl in next_level:
        family_count = family_count + 1
        parse_next_level(nl, conn, family_group, family_count, parent_id, date_recorded)
        is_next_level = nl.find("ul")
        if is_next_level:
            nl.ul.find_all("li", recursive=False)
            family_count = get_next_level(nl.ul.find_all("li", recursive=False), conn, family_group, family_count, family_count, date_recorded)
    return family_count

def main():
    """ main function scrapes forum
    :return: nothing
    """
    family_group = 1
    page = 1
    db_file = "../database/rawCrawl.db"
    conn = create_connection(db_file)
    set_up_db(conn)
    # connect to forum
    forum_url = "https://www.youbemom.com/forum/special-needs"
    next_url = forum_url[:]
    earliest = datetime(2019, 8, 15, 0, 0, 0)
    family_count = 1
    scraped_earliest = False
    while not scraped_earliest:
        print("page: " + str(page))
        soup = get_soup(next_url)
        top_posts = get_top_posts(soup)
        date_recorded = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        # parse each main list item
        for li in top_posts:
            print(li)
            date_created = parse_top_post(li, conn, family_group, date_recorded)
            parent_id = 1
            is_next_level = li.find("ul")
            if is_next_level:
                next_level = li.ul.find_all("li", recursive=False)
                get_next_level(next_level, conn, family_group, family_count, parent_id, date_recorded)
            family_group = family_group + 1
        scraped_earliest = date_created < earliest
        page = page + 1
        next_url = forum_url + "?pg=" + str(page)
        sleep(3)

# Run program

if __name__ == '__main__':
    main()
