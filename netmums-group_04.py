#!/usr/bin/env python3
# coding: utf-8

## Imports

from netmums import *
from scraping import *
from pathlib import Path

## File Locations

p = Path.cwd()
path_parent = p.parents[0]
path_db_parent = str(path_parent / "database" / "netmums-merged.db")
path_db_child = str(path_parent / "database" / "netmums04.db")

## Connect to the database and create the tables.

### find max id in child db posts
conn = create_connection(path_db_child)
set_up_posts_db(conn)
cur = conn.cursor()
cur.execute(''' SELECT MAX(thread_id) FROM posts ''')
max_thread = cur.fetchone()[0]
if max_thread == None:
    first = 791497
else: # restart scraping from last complete thread id
    cur.execute(''' DELETE FROM posts WHERE thread_id=?''', (max_thread,))
    conn.commit()
    first = max_thread
conn.close()

### select rows from parent db threads
conn = create_connection(path_db_parent)
cur = conn.cursor()
cur.execute(''' SELECT id, url FROM threads WHERE id>=? AND id<=1055328 ''', (first,))
rows = cur.fetchall()
conn.close()

### connect back to child db
conn = create_connection(path_db_child)
set_up_posts_db(conn)

## Scrape threads

for row in rows:
    scrape_posts(conn, row)

conn.close()
