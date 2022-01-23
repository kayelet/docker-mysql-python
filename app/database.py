import mysql.connector as mysql
import logging
import re
import os
from collections import Counter
from datetime import datetime


class Database:
    def __init__(self, database, host, port, user, password, sqls_dir):
        self.db = mysql.connect(
            host=host,
            port=port,
            user=user,
            passwd=password,
            database=database
        )
        self.sqls_dir = sqls_dir
        self.cursor = self.db.cursor()
        self.db.autocommit = False
        self.logging = logging.basicConfig(level=50)

    def exit_program(self, exit_code):
        """ Exit program with success/failure exit code """
        print(f"\nexit {exit_code}")
        self.cursor.close()
        self.db.close()
        exit(exit_code)

    def close_db(self):
        """ Exit program with success/failure exit code """
        print("\nexit")
        self.cursor.close()
        self.db.close()

    def create_log_table(self):
        """ Create SQL_RUN_LOG table """
        sql_file = f"{self.sqls_dir}/sql_run_log_0.sql"
        print("Creating SQL_RUN_LOG table.")
        try:
            f = open(sql_file)
            f.close()
        except FileNotFoundError:
            print('File sql_run_log_0.sql does not exist, check your SQL files directory.')
            self.exit_program(1)

        with open(sql_file) as sql:
            sql_command = sql.read()
            try:
                self.cursor.execute(sql_command)
                print("SQL_RUN_LOG created successfully.\n")
            except mysql.DatabaseError as error:
                print("\nERROR: failed to create table SQL_RUN_LOG: ", error.msg)
                self.exit_program(1)

    def get_last_run_script_id(self):
        """ get the ID of last SQL file that
            ran successfully on database so current process will run
            the SQL files that should run next
        """
        last_id_tup = (0, None)
        self.cursor.execute("SHOW TABLES LIKE 'SQL_RUN_LOG'")
        if len(self.cursor.fetchall()) == 0:
            self.create_log_table()
        self.cursor.execute("select run_id, sql_name from SQL_RUN_LOG where "
                            "run_id=(select max(run_id) from SQL_RUN_LOG where run_status='SUCCESS')")
        res = self.cursor.fetchall()  # [0][0]
        if res:
            last_id_tup = res[0]
            print("\nlast applied RUN_ID found in SQL_RUN_LOG: ", last_id_tup)

        return last_id_tup

    def verify_scripts_run_id_uniqueness(self, files_list):
        """ Verify each SQL file has a unique ID """
        run_id_counts = Counter([script.split('.sql')[0].split('_')[-1] for script in files_list])
        logging.debug("run_id_counts: {}".format(run_id_counts))
        logging.debug("files_list: {}".format(files_list))
        duplicate_run_ids = [(key, value) for key, value in dict(run_id_counts).items() if value > 1]
        if duplicate_run_ids:
            print("ERROR: Duplicate RUN_IDs found as follows:")
            for dup_ext in duplicate_run_ids:
                print(f"-- Extension _{dup_ext[0]}.sql found in {dup_ext[1]} SQL scripts, as follows:")
                print(*[file for file in files_list if file.endswith(f"_{dup_ext[0]}.sql")], sep="\n")
            self.exit_program(1)

    def verify_valid_run_id_gaps(self, files_list, last_script_id_tup):
        files_list_copy = files_list[:]
        logging.debug("last_script_id_tup: {}".format(last_script_id_tup))
        if not last_script_id_tup[1]:  # log table is empty
            files_list_copy.insert(0, "sql_run_log_0.sql")
            if int(files_list[0].split('.sql')[0].split('_')[-1]) > 10:
                print(
                    "GAP ERROR: no records found in SQL_RUN_LOG; first sql file to run must be with RUN_ID between 1 and 10.")
                self.exit_program(1)
        else:  # checking gap between last run id and first sql script the user wishes to run
            files_list_copy.insert(0, last_script_id_tup[1])

        logging.debug("sql copy list: {}".format(files_list_copy))
        run_id_list = [int(sql_file.split('.sql')[0].split('_')[-1]) for sql_file in files_list_copy]
        logging.debug("run_id_list: {}".format(run_id_list))
        run_id_gaps = [j - i for i, j in zip(run_id_list[:-1], run_id_list[1:])]
        logging.debug("run_id_gaps: {}".format(run_id_gaps))
        wide_run_id_tups = [(files_list_copy[i], files_list_copy[i + 1])
                            for i, gap in enumerate(run_id_gaps) if gap > 10]
        if wide_run_id_tups:
            print("GAP ERROR: the following SQL files have to wide RUN_ID gaps (maximum of 10 is allowed):")
            print(wide_run_id_tups, sep="\n")
            self.exit_program(1)

    def generate_scripts_list(self, last_script_id_tup, i_sqls):
        """ Generate the list of the SQL files that should run
            on database. SQL files must comply with name pattern
        """

        pattern = re.compile(r"[a-z]+[a-z0-9_]+_[0-9]+\.sql$")
        sql_files = []
        if i_sqls:
            if not os.path.isdir(i_sqls) and not os.path.isfile(i_sqls):
                print(f"ERROR: file/directory {i_sqls} not found.")
                self.exit_program(1)

            if os.path.isfile(i_sqls):
                if '/' in i_sqls: # file as path
                    self.sqls_dir = os.path.dirname(i_sqls)
                    sql_files.append(os.path.basename(i_sqls))
            else:
                self.sqls_dir = i_sqls

        if not sql_files:
            sql_files = [file for file in os.listdir(self.sqls_dir)]

        valid_sql_files = [file for file in sql_files if pattern.fullmatch(file) and
                           file != 'sql_run_log_0.sql' and
                           int(str(file).split('.sql')[0].split('_')[-1]) > last_script_id_tup[0]]
        if not valid_sql_files:
            print(f"No valid SQL files found.")
            print(f"** valid: matches valid name pattern ([a-z]+[a-z0-9_]+_[0-9]+.sql) and has RUN_ID higher than {last_script_id_tup[0]}.")
            self.exit_program(0)

        valid_sql_files.sort(key=lambda sql_file: int(str(sql_file).split('.sql')[0].split('_')[-1]))
        logging.debug("valid sql files list: {}".format(valid_sql_files))

        print("\nValid SQL files:")
        print(*valid_sql_files, sep="\n")
        print("")
        self.verify_scripts_run_id_uniqueness(valid_sql_files)
        self.verify_valid_run_id_gaps(valid_sql_files, last_script_id_tup)
        return valid_sql_files

    def write_to_sql_run_log(self, run_id: int, sql_file: str, status: str, error_msg: str):
        """ Write the SQL file and its result (SUCCESS/FAILURE) in the log table
            SQL_RUN_LOG
        """
        try:
            self.cursor.execute("select exists(select 1 from SQL_RUN_LOG where run_id=%s)", (run_id,))
            run_id_exists = self.cursor.fetchall()[0][0]
        except mysql.DatabaseError as error:
            print("ERROR: failed to get run id: ", error.msg)
            self.exit_program(1)
        try:
            if run_id_exists:
                self.cursor.execute(
                    "REPLACE INTO SQL_RUN_LOG (run_id, sql_name, run_status, error_message, date) VALUES "
                    "(%s, %s, %s, %s, %s)", (run_id, sql_file, status, error_msg, datetime.now()))
                self.db.commit()
            else:
                self.cursor.execute(
                    "INSERT INTO SQL_RUN_LOG (run_id, sql_name, run_status, error_message, date) VALUES "
                    "(%s, %s, %s, %s, %s)", (run_id, sql_file, status, error_msg, datetime.now()))
                self.db.commit()
        except mysql.DatabaseError as error:
            print("ERROR: failed to insert SQL_RUN_LOG: ", error.msg)
            self.exit_program(1)

    def run_statement(self, statement, run_id, sql_file):
        try:
            self.cursor.execute(statement)
        except mysql.Error as error1:
            print(f"\nERROR: failed to run {sql_file}: ", error1.msg)
            try:
                self.db.rollback()
                print(f"-- All DML statements in {sql_file} are rolled back.")
                print("")
            except mysql.DatabaseError as error:
                print("\nERROR: failed to rollback: ", error.msg)
                print("\nHandle manually!")
                self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="FAILED",
                                          error_msg=error.msg)
                self.exit_program(1)
            self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="FAILED",
                                      error_msg=error1.msg)
            self.exit_program(1)

    def run_sql_files_on_database(self, sql_files):
        """ Find and run relevant SQL files on DB """

        for sql_file in sql_files:
            run_id = int(sql_file.split('.sql')[0].split('_')[-1])
            print(f"Running {sql_file}.. run_id: {run_id}; ", end="")
            with open(f"{self.sqls_dir}/{sql_file}") as sql:
                sql_command = sql.read()
                logging.debug("sql command READ file: ", sql_command)
                if not sql_command.replace(";", "").strip():  # file contains no statements
                    print(f"ERROR: failed to run {sql_file}: file contains no statements.")
                    self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file,
                                              status="FAILED", error_msg="ERROR: SQL file contains NO statements.")
                    self.exit_program(1)
                for statement in sql_command.split(';'):
                    if not statement.strip(): # empty statement
                        continue
                    else:
                        self.run_statement(statement, run_id, sql_file)
            print("OK.")
            self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="SUCCESS", error_msg="")
