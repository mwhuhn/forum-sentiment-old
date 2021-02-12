#!/usr/bin/env python3
# coding: utf-8

# Contains functions for scraping Netmums forum posts

import re
import sqlite3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil.parser import parse
from scraping import *

## Regex

skip = re.compile(r'(product tests|becoming a mum|faq|research requests)', re.IGNORECASE)
sent_from = re.compile(r'sent\s+from\s+my\s+[a-z0-9\-]*\s+using\s+netmums\s+mobile\s+app', re.IGNORECASE)
shortened_url = re.compile(r'\[\.\.\.\]', re.IGNORECASE)
extra_spaces = re.compile(r'\s+')
url_id = re.compile(r'#post([0-9]+)')

## Functions for creating and writing to the database

def set_up_posts_db(conn):
	""" sets up tables in netmums database to be merged later
		if the table doesn't exists, create it
	:param conn: database connection
	:return: nothing
	"""
	cur = conn.cursor()
	cur.executescript('''
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			name TEXT,
			data_user_id TEXT,
			url TEXT
		);
		CREATE TABLE IF NOT EXISTS posts(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			thread_id INTEGER,
			post_id TEXT,
			post_count TEXT,
			data_user_id TEXT,
			date_created TEXT,
			date_recorded TEXT,
			body TEXT
		);
		CREATE TABLE IF NOT EXISTS quotes(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			quoting_id TEXT,
			quoted_id TEXT
		);
	''')

def set_up_merged_db(conn):
	""" sets up tables in netmums database
		if the table doesn't exists, create it
	:param conn: database connection
	:return: nothing
	"""
	cur = conn.cursor()
	cur.executescript('''
		CREATE TABLE IF NOT EXISTS forums (
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			url TEXT,
			name TEXT
		);
		CREATE TABLE IF NOT EXISTS subforums (
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			url TEXT,
			name TEXT,
			forum_id INTEGER
		);
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			name TEXT,
			data_user_id TEXT,
			url TEXT
		);
		CREATE TABLE IF NOT EXISTS threads(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			url TEXT,
			subject TEXT,
			subforum_id INTEGER
		);
		CREATE TABLE IF NOT EXISTS posts(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			thread_id INTEGER,
			post_id TEXT,
			post_count TEXT,
			data_user_id TEXT,
			date_created TEXT,
			date_recorded TEXT,
			body TEXT
		);
		CREATE TABLE IF NOT EXISTS quotes(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
			quoting_id TEXT,
			quoted_id TEXT
		);
	''')

def write_citation(cur, quoting_id, quoted_id):
	""" writes citation ids to the quotes table,
		links quoted posts to the quoting posts
	:param quoting_id: id of post quoting another post
	:param quoted_id: id of post being quoted
	:return: nothing
	"""
	parsed = (quoting_id, quoted_id)
	sql = '''
		INSERT INTO quotes(quoting_id, quoted_id)
		VALUES(?,?)
	'''
	cur.execute(sql, parsed)

def write_post(cur, thread_id, post_id, post_count, data_user_id, date_created, body):
	""" writes post information to posts table
	:param thread_id: id of thread, linked to threads table
	:param post_id: id scraped from post, linked to quotes table
	:param post_count: count of post in thread
	:param data_user_id: user id number, linked to users table
	:param date_created: date post was created
	:param date_recorded: date post was recorded
	:param body: text body of post
	:return: nothing
	"""
	date_recorded = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	parsed = (thread_id, post_id, post_count, data_user_id, date_created, date_recorded, body)
	sql = '''
		INSERT INTO posts(thread_id, post_id, post_count, data_user_id, date_created, date_recorded, body)
		VALUES(?,?,?,?,?,?,?)
	'''
	cur.execute(sql, parsed)

def write_user(cur, name, data_user_id, url):
	""" write user information to users table
	:param url: url of profile
	:param name: string of name
	:data_user_id: id of user, linked to posts table
	:note: does not check for duplicates,
		will delete duplicates after scrape
		to make writing quicker
	"""
	parsed = (name, data_user_id, url)
	sql = '''
		INSERT INTO users(name, data_user_id, url)
		VALUES(?,?,?)
	'''
	cur.execute(sql, parsed)

## Functions for scraping Netmums

### Forum

def keep_forum(name):
	""" skips or keeps forum based on forum name
	:param name: forum name
	:return: bool keep or skip
	"""
	if re.search(skip, name):
		return False
	else:
		return True

### Threads

def scrape_threads(cur, row):
	""" scrape information on threads from list of subforums
	:param row: row selected from subforum table
	:return: nothing
	"""
	page = 1
	(subforum_id, url) = row
	next_url = url + "index{}.html"
	soup = get_soup(url)
	not_end = True
	while not_end:
		print("page", page)
		if soup.find("a", {"class": "cCatTopic"}):
			for thread in soup.find_all("td", {"class": "sujetCase3"}):
				link = thread.find("a", {"class": "cCatTopic"})
				parsed = (link['href'], link.get_text(), subforum_id)
				sql = '''
					INSERT INTO threads(url,subject,subforum_id)
					VALUES(?,?,?)
				'''
				cur.execute(sql, parsed)
			page += 1
			soup = get_soup(next_url.format(str(page)))
		else:
			not_end = False

### Posts

def get_next_url(soup):
	""" get the next page url in the thread, else False
	:param soup: soup of the current page
	:return: the next url or False, if no next url
	"""
	next_button = soup.find("div", {"class":"pagepresuiv_next"})
	if link := next_button.find("a"):
		next_url = link.get('href')
		return next_url
	return False

def get_user(cur, soup):
	""" get the user from the post
	:param soup: soup of the current page
	:return: the post's user name, data user id, and url
	:note: writes user to database
	"""
	user = soup.find("span", {"class": "CF_user_mention"}, recursive=True)
	if not user:
		data_user_id = "NA"
	else:
		user_name = user.get_text()
		data_user_id = user['data-id_user']
		avatar = soup.find("div", {"class","avatar_center"})
		img = avatar.find("img")
		url = img.get("alt")
		write_user(cur, user_name, data_user_id, url)
	return data_user_id

def get_date(soup):
	""" get the date from the post
	:param soup: soup of the current page
	:return: the post's date created formatted Y-M-D H:MP
	"""
	date = soup.find("span", {"class": "topic_posted"}, recursive=True)
	time = re.sub("(Posted on\s|at\s)", "", date.get_text()).strip()
	time = re.sub("\s+", " ", time)
	time = datetime.strptime(time, "%d-%m-%Y %I.%M%p" ).strftime("%Y-%m-%d %I:%M%p")
	return time

def strip_text(text):
	""" strips the text of extra spaces and "sent from" text
	:param text: text to clean
	:return: striped text
	"""
	clean = re.sub(sent_from, "", text).strip()
	return re.sub(extra_spaces, " ", clean)

def is_shortened_url(text):
	""" checks if the url in the text is a shorted url "[...]"
	:param text: text of url
	:return: bool
	"""
	if re.search(shortened_url, text):
		return True
	else:
		return False

def get_post_id(post):
	""" finds the id of the post from the post content
	:param post: post content div
	:return: id of post
	"""
	post_id = re.sub("para", "", post['id'])
	return post_id

def get_citations(cur, post, post_id):
	""" finds the citations in a post
	:param post: post content div
	:param post_id: post id
	:return: length of citations list
	:note: writes citations to quotes table
	"""
	citations = post.find_all("span", {"itemprop": "citation"})
	for cite in citations:
		cite_url = cite.find("span", {"itemprop": "url"}).get_text()
		cite_id = id_from_url(cite_url)
		write_citation(cur, post_id, cite_id)
	return len(citations)

def id_from_url(text):
	""" finds the id of the post from the url
	:param text: text of url
	:return: id of quoted post or empty string if not found
	"""
	quote_id = re.search(url_id, text)
	if quote_id:
		return quote_id.group(1)
	return ""

def replace_emojis(div):
	""" finds any wysiwyg emojis in the body and
		replaces them with text representation
	:param div: post body div
	:return: div cleaned of emojis
	"""
	imgs = div.find_all("img", {"class":"wysiwyg_smiley"})
	for img in imgs:
		if img.has_attr("title"):
			img.string = img.get("title")
	return div

def replace_hrefs(div):
	""" finds any links in the body with shortened urls
		and replaces them with the full url
	:param div: post body div
	:return: div cleaned of shortened urls
	"""
	hrefs = div.find_all("a")
	for href in hrefs:
		if is_shortened_url(href.get_text()):
			href.string = href.get("href")
	return div

def get_text_no_cite(post):
	""" finds the text from posts with no citations
	:param post: post soup
	:return: cleaned body text
	"""
	div = post.find("div")
	div = replace_emojis(div)
	div = replace_hrefs(div)
	text = ""
	for child in div.children:
		if isinstance(child, NavigableString):
			text = text + " " + child
		else:
			text = text + " " + child.get_text(separator=" ")
	return strip_text(text)

def get_text_cite(post):
	""" finds the text from posts with citations
	:param post: post soup
	:return: cleaned body text
	"""
	div = post.find("div")
	div = replace_emojis(div)
	div = replace_hrefs(div)
	para = div.find_all("p")
	text = ""
	for p in para:
		text = text + " " + p.get_text(separator=" ")
	return strip_text(text)

def scrape_posts(conn, row):
	""" scrape information on posts from threads table
	:param row: row from threads table
	:return: nothing
	"""
	cur = conn.cursor()
	(thread_id, url) = row
	next_url = url
	post_count = 0
	page = 0
	while next_url:
		page += 1
		soup = get_soup(next_url)
		error404 = soup.find("div", {"class","error-404"})
		if error404:
			break
		next_url = get_next_url(soup) # returns False if no next url
		cases = soup.find_all("div", {"class","md-topic_post"})
		for case in cases:
			post_count += 1
			if page > 1 and post_count == 1: # skip dup posts on top of page
				continue
			data_user_id = get_user(cur, case)
			date_created = get_date(case)
			post = case.find("div", {"class": "post_content"})
			post_id = get_post_id(post)
			len_citations = get_citations(cur, post, post_id)
			if len_citations == 0:
				text = get_text_no_cite(post)
			else:
				text = get_text_cite(post)
			write_post(cur, thread_id, post_id, post_count, data_user_id, date_created, text)
			conn.commit()