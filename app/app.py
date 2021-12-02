from typing import List, Dict
from flask import Flask, jsonify, request
import mysql.connector
import json
import os
from datetime import datetime
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
    try:
        conn.cursor.execute("SELECT run_id, sql_name, error_message, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                            "FROM sql_run_log where run_status='FAILED'")
        results = [{'run_id': run_id, 'sql_name': sql_name, 'error_message': error_message, 'date': date}
                   for (run_id, sql_name, error_message, date) in conn.cursor]
    except mysql.connector.Error as err:
        results = [{"ERROR": err.msg}]

    conn.cursor.close()
    conn.db.close()
    return results


def get_success_sqls() -> List[Dict]:
    conn = Database(**config)
    try:
        conn.cursor.execute("SELECT run_id, sql_name, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                            "FROM sql_run_log where run_status='SUCCESS'")
        results = [{'run_id': run_id, 'sql_name': sql_name, 'date': date}
                   for (run_id, sql_name, date) in conn.cursor]
    except mysql.connector.Error as err:
        results = [{"ERROR": err.msg}]
    print("results: ", results)
    conn.cursor.close()
    conn.db.close()
    return results

def get_sql_log(runid):
    conn = Database(**config)
    try:
        conn.cursor.execute("SELECT run_id, sql_name, run_status, error_message, DATE_FORMAT(date, '%Y-%m-%d %h:%i:%s') "
                            f"FROM sql_run_log where run_id={runid}")
        results = [{'run_id': run_id, 'sql_name': sql_name, 'run_status': run_status,
                    'error_message': error_message, 'date': date}
                   for (run_id, sql_name, run_status, error_message, date) in conn.cursor]
        # print("results, len: ", results, len(results))
    except mysql.connector.Error as err:
        results = [{"ERROR": err.msg}]

    conn.cursor.close()
    conn.db.close()
    return results

def drop_tables() -> List[Dict]:
    conn = Database(**config)
    sqls_drop = []
    errors = set()
    with open(f"{conn.sqls_dir}/drop_tables.sql") as drop_tabs_file:
        drop_commands = drop_tabs_file.read()
        if not drop_commands.strip():
            return [{'ERROR: ': f'File {conn.sqls_dir}/drop_tables.sql is empty.'}]
        for statement in drop_commands.split(';')[::-1]:
            i=0
            if statement:
                try:
                    print(f"Running {statement}")
                    conn.cursor.execute(statement)
                    print("  OK.")
                    success = True
                    sqls_drop.append({'statement': statement, 'status': 'OK', 'i': f"{i}"})
                    i += 1
                #except mysql.connector.DatabaseError as error:
                except mysql.connector.Error as err:
                    i += 1
                    if err.errno == 1051: # table does not exist
                        errors.add(err.errno)
                        continue
                    else:
                        sqls_drop.append({'statement': statement, 'ERROR': f'{err.errno} - {err.msg}'})

    if not sqls_drop and errors:
        sqls_drop.append({'Not dropped': 'Tables already dropped.'})

    conn.cursor.close()
    conn.db.close()
    return sqls_drop

def update_runid_to_success(runid):
    conn = Database(**config)
    try:
        #now = datetime.now()
        conn.cursor.execute(
            f"update sql_run_log set run_status=%s, date=%s where run_id={runid}"
        ,("SUCCESS", datetime.now()))
        #("""UPDATE mytable2 rec_open_date=%s WHERE rec_id=%s""",
        # (open_dt, rec_id))
        if conn.cursor.rowcount == 0:
           results = [{"ERROR": f"A record with RUN_ID {runid} not found."}]
        else:
           results = [{"SUCCESS": f"Record updated."}]

            # for (run_id, sql_name, run_status, error_message, date) in conn.cursor]
        # print("results, len: ", results, len(results))
    except mysql.connector.Error as err:
        results = [{"ERROR": err.msg}]

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

@app.route('/drop_tables', methods=['GET','DELETE'])
def drop_db_tables():
    drop_sql_file = f"/tmp/drop_tables.sql"
    if not os.path.isfile(drop_sql_file):
        return jsonify(error={"Not found": f"Drop file {drop_sql_file} not found."})
    else:
        drp = drop_tables()
        return jsonify({"drop_tables": drp})

@app.route('/update-to-success', methods=['GET','PATCH'])
def update_runid_status():
    id = request.args.get("id")
    return jsonify(update_run_id=update_runid_to_success(id))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    #app.run(host='localhost', debug=True)