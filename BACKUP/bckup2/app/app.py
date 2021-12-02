from typing import List, Dict
from flask import Flask, jsonify
import mysql.connector
import json
import os
from database import Database

#connection = Database(database="mysql_db", host="db", port="3306", user="root", password="root", sqls_dir="/tmp")

config = {
        "user": "root",
        "password": "root",
        "host": "db",
        "port": "3306",
        "database": "mysql_db",
        "sqls_dir": "/tmp"
    }
app = Flask(__name__)
#app.connection = Database(database="mysql_db", host="db", port="3306", user="root", password="root", sqls_dir="/tmp")



def favorite_colors() -> List[Dict]:
    #host = 'db' #os.environ.get('DB_HOST')
    #self.sqls_dir = sqls_dir
    # self.cursor = self.db.cursor()
    #conn = mysql.connector.connect(**config)
    conn = Database(**config)
    #cursor = conn.cursor()
    conn.cursor.execute('SELECT * FROM favorite_colors')
    #print("connection.cursor: ", cursor)
    results = [{name: color} for (name, color) in conn.cursor]
    conn.cursor.close()
    conn.db.close()
    return results


@app.route('/')
def index() -> str:
    return json.dumps({'favorite_colors': favorite_colors()})

@app.route('/failed')
def get_failed_sql():
    conn = Database(**config)
    conn.cursor.execute("SELECT run_id, sql_name, error_message, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                   "FROM sql_run_log where run_status='FAILED'")
    #print("connection.cursor: ", cursor)

    results = conn.cursor.fetchall()
    print("results: ", results)
    conn.cursor.close()
    conn.db.close()
    return jsonify(failed_SQL=[{'run_id': item[0], 'sql_name': item[1], 'error_message': item[2], 'date': item[3]}
                               for item in results])

    # last_run_script_id = connection.get_last_run_script_id()
    # scripts_list = connection.generate_scripts_list(last_run_script_id)
    # if not scripts_list:
    #     connection.exit_program(0)
    #     return json.dumps({'RUN_STATUS': 'Nothing to run.'})

    # connection.run_sql_files_on_database()
    # return json.dumps({'RUN_STATUS': connection.run_sql_files_on_database()})

@app.route('/success')
def get_success_sqls():
    conn = Database(**config)
    conn.cursor.execute("SELECT run_id, sql_name, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                   "FROM sql_run_log where run_status='SUCCESS'")

    #print("connection.cursor: ", cursor)

    results = conn.cursor.fetchall()
    print("results: ", results)

    conn.cursor.close()
    conn.db.close()
    return jsonify(data=[{'run_id': item[0], 'sql_name': item[1], 'date': item[2]} for item in results])

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)