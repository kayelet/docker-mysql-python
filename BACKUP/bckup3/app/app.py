from typing import List, Dict
from flask import Flask, jsonify, request
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


def favorite_colors() -> List[Dict]:
    conn = Database(**config)
    conn.cursor.execute('SELECT * FROM favorite_colors')
    results = [{name: color} for (name, color) in conn.cursor]
    conn.cursor.close()
    conn.db.close()
    return results


def get_failed_sql() -> List[Dict]:
    conn = Database(**config)
    conn.cursor.execute("SELECT run_id, sql_name, error_message, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                        "FROM sql_run_log where run_status='FAILED'")
    # results = conn.cursor.fetchall()
    results = [{'run_id': run_id, 'sql_name': sql_name, 'error_message': error_message, 'date': date}
               for (run_id, sql_name, error_message, date) in conn.cursor]
    print("results: ", results)
    conn.cursor.close()
    conn.db.close()
    return results


def get_success_sqls() -> List[Dict]:
    conn = Database(**config)
    conn.cursor.execute("SELECT run_id, sql_name, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                        "FROM sql_run_log where run_status='SUCCESS'")
    results = [{'run_id': run_id, 'sql_name': sql_name, 'date': date}
               for (run_id, sql_name, date) in conn.cursor]
    print("results: ", results)
    conn.cursor.close()
    conn.db.close()
    return results

def get_sql_log(runid):
    conn = Database(**config)
    conn.cursor.execute("SELECT run_id, sql_name, run_status, error_message, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                        f"FROM sql_run_log where run_id={runid}")
    results = [{'run_id': run_id, 'sql_name': sql_name, 'run_status': run_status,
                'error_message': error_message, 'date': date}
               for (run_id, sql_name, run_status, error_message, date) in conn.cursor]
    print("results, len: ", results, len(results))
    conn.cursor.close()
    conn.db.close()
    return results


@app.route('/')
def index() -> str:
    return json.dumps({'favorite_colors': favorite_colors()})


@app.route('/failed')
def failed_sql():
    return jsonify({"failed_sql": get_failed_sql()})


@app.route('/success')
def success_sqls():
    return jsonify({"success_sqls": get_success_sqls()})

@app.route('/run_id')
def search_run_id_row():
    id = request.args.get("id")
    sql_log = get_sql_log(id)
    if sql_log:
        return jsonify({"sql log": get_sql_log(id)})
    else:
        return jsonify(error={"Not found": f"No SQL with run_id {id} found in DB."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)