earliest = 9526938 # fix to start 2018/01/01: 9454476
latest = 10991517
groups = 30
size = round((latest-earliest)/groups)

text = """
## Imports

from youbemom import loop_link_threads, create_connection, set_up_db
from pathlib import Path

## File Locations

p = Path.cwd()
path_parent = p.parents[0]
path_db = path_parent / "database" / "youbemomTables-{0}.db"
path_db = str(path_db)

## Connect to the database and create the tables.

conn = create_connection(path_db)
set_up_db(conn)

## Scrape threads

earliest_link = {1}
last_link = {2}
loop_link_threads(conn, path_db, earliest_link, last_link)

conn.close()
"""

with open("run_groups.sh", 'a') as b:
    b.write("#!/bin/sh\n")

for g in range(groups):
    first = earliest + (size * g)
    if g == groups - 1:
        last = latest
    else:
        last = earliest + (size * (g + 1))
    if g + 1 < 10:
        num = "0{}".format(g + 1)
    else:
        num = "{}".format(g + 1)
    with open("group_{}.py".format(num), 'w') as w:
        w.write(text.format(num, first, last))
    with open("run_groups.sh", 'a') as b:
        b.write("nohup krenew -t -- python3 group_{0}.py > output_{1}.txt &\n".format(num, num))