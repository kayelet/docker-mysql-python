from typing import List, Dict
from flask import Flask, jsonify
import mysql.connector
import json
import os
from database import Database

app = Flask(__name__)


def favorite_colors() -> List[Dict]:
    #host = 'db' #os.environ.get('DB_HOST')
    sqls_dir = '/tmp'
    #conn = Database(database='mysql_db', host="3200", port='3306', user='root', password='root', sqls_dir=sqls_dir)

    config = {
        "user": "root",
        "password": "root",
        "host": "db",
        "port": "3306",
        "database": "mysql_db"
    }
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM favorite_colors')
    results = [{name: color} for (name, color) in cursor]
    cursor.close()
    connection.close()
    return results
    # {
    #     'user': 'root',
    #     'password': 'root', #os.environ.get('MYSQL_ROOT_PASSWORD'),
    #     'host': os.environ.get('DB_HOST'),
    #     'port': '3306',
    #     'database': 'mysql_db' #os.environ.get('MYSQL_DATABASE')
    # }

    # 'password': 'root',
    # 'host': 'db',
    # 'port': '3306',
    # 'database': 'knights'
    #connection = mysql.connector.connect(**config)

    # cursor = conn.cursor()
    # cursor.execute('SELECT * FROM favorite_colors')
    # results = [{name: color} for (name, color) in cursor]
    # cursor.close()
    # conn.db.close()

    #return results


@app.route('/')
def index() -> str:
    return json.dumps({'favorite_colors': favorite_colors()})


if __name__ == '__main__':
    app.run(host='0.0.0.0')