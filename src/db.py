import sqlite3
import config
import os
from settings import settings
from pprint import pprint


def execute_queries(queries):
    conn = sqlite3.connect(os.path.join(config.BASE_DIR, config.DATA_DIR, settings['database']))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    for query in queries:
        if query.param is not None:
            c.execute(query.command, query.param)
        else:
            c.execute(query.command)

        if "one" == query.result:
            data = c.fetchone()
        elif "insert" == query.result:
            data = c.lastrowid
        elif "update" == query.result:
            data = None
        else:
            data = c.fetchall()

        conn.commit()

    conn.close()

    return data


class Query:
    def __init__(self, command, param=None, result="all"):
        self.command = command
        self.param = param
        self.result = result
