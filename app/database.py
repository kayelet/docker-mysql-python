#from mysql import secret_lazy_loaded_submodule
import mysql.connector as mysql
from mysql.connector.locales.eng import client_error

import re
import os
from collections import Counter
from datetime import datetime


class Database:
    def __init__(self, database, host, port, user, password, sqls_dir):
        # self.db = mysql.connect(
        #     host={},
        #     port={},
        #     user={},
        #     passwd={},
        #     database={}
        # ).format(host, port, user, password, database)
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
        self.cursor.execute("SHOW TABLES LIKE 'sql_run_log'")
        if len(self.cursor.fetchall()) == 0:
            self.create_log_table()
        self.cursor.execute("select run_id, sql_name from sql_run_log where "
                            "run_id=(select max(run_id) from sql_run_log where run_status='SUCCESS')")
        res = self.cursor.fetchall()  # [0][0]
        if res:
            last_id_tup = res[0]
            print("last id: ", last_id_tup)

        return last_id_tup

    def verify_scripts_run_id_uniqueness(self, files_list):
        """ Verify each SQL file has a unique ID """
        run_id_counts = Counter([script.split('.sql')[0].split('_')[-1] for script in files_list])
        print("run_id_counts", run_id_counts)
        print("files_list: ", files_list)
        duplicate_run_ids = [(key, value) for key, value in dict(run_id_counts).items() if value > 1]
        if duplicate_run_ids:
            print("ERROR: Duplicate RUN_IDs found as follows:")
            for dup_ext in duplicate_run_ids:
                print(f"   Extension _{dup_ext[0]}.sql found in {dup_ext[1]} SQL scripts.")
            self.exit_program(1)

    def verify_valid_run_id_gaps(self, files_list, last_script_id_tup):
        files_list_copy = files_list[:]
        print("last_script_id_tup: ", last_script_id_tup)
        if not last_script_id_tup[1]:
           files_list_copy.insert(0, "sql_run_log_0.sql")
        else: # in case no rows in run_Sql_log table, checking gap between 0 and first sql script the user wishes to run
            if int(files_list[0].split('.sql')[0].split('_')[-1]) > 10:
                print("No records found in SQL_RUN_LOG; first sql file to run must not be with RUN_ID greater than 10.")
                self.exit_program(1)

        print("sql copy list: ", files_list_copy)
        run_id_list = [int(sql_file.split('.sql')[0].split('_')[-1]) for sql_file in files_list_copy]
        print("run_id_list: ", run_id_list)
        # print("run id list with last run_id: ", run_id_list)
        run_id_gaps = [j - i for i, j in zip(run_id_list[:-1], run_id_list[1:])]
        wide_run_id_tups = [(files_list_copy[i], files_list_copy[i + 1]) for i, gap in enumerate(run_id_gaps) if gap > 10]
        if wide_run_id_tups:
            print("The following SQL files have to wide RUN_ID gaps (maximum of 10 is allowed):")
            print(wide_run_id_tups, sep="\n")
            self.exit_program(1)


    def generate_scripts_list(self, last_script_id_tup, i_sqls=None):
        """ Generate the list of the SQL files that should run
            on database. SQL files must comply with name pattern
        """

        regex = re.compile(".+_[0-9]+\.sql$")
        sql_files = []

        if i_sqls:
            if not os.path.isdir(i_sqls) and not os.path.isfile(i_sqls):
                print(f"ERROR: file/directory {i_sqls} not found.")
                self.exit_program(1)

            if os.path.isfile(i_sqls):
                sql_files.append(i_sqls)
            else:
                self.sqls_dir = i_sqls

        if not sql_files:
            # print("files in dir: ")
            # print(os.listdir(self.sqls_dir))
            sql_files = [file for file in os.listdir(self.sqls_dir)]

        valid_sql_files = [file for file in sql_files if regex.match(file) and
                           int(str(file).split('.sql')[0].split('_')[-1]) > last_script_id_tup[0]]
        if not valid_sql_files:
            print(f"No valid SQL files found.")
            print(f"** valid: with expected name pattern or with RUN_ID higher than {last_script_id_tup[0]}.")
            self.exit_program(0)

        valid_sql_files.sort(key=lambda sql_file: int(str(sql_file).split('.sql')[0].split('_')[-1]))
        print("valid sql files list: ", valid_sql_files)

        self.verify_scripts_run_id_uniqueness(valid_sql_files)
        self.verify_valid_run_id_gaps(valid_sql_files, last_script_id_tup)
        # print("AFTER GAP validation: ", valid_sql_files)
        return valid_sql_files

    def write_to_sql_run_log(self, run_id: int, sql_file: str, status: str, error_msg: str):
        """ Write the SQL file and its result (SUCCESS/FAILURE) in the log table
            SQL_RUN_LOG
        """
        try:
            self.cursor.execute("select exists(select 1 from sql_run_log where run_id=%s)", (run_id,))
            run_id_exists = self.cursor.fetchall()[0][0]
        except mysql.DatabaseError as error:
            print("ERROR: failed to get run id: ", error.msg)
            self.exit_program(1)
        try:
            if run_id_exists:
                print("REPLACE")
                self.cursor.execute(
                    "REPLACE INTO sql_run_log (run_id, sql_name, run_status, error_message, date) VALUES "
                    "(%s, %s, %s, %s, %s)", (run_id, sql_file, status, error_msg, datetime.now()))
                self.db.commit()
            else:
                self.cursor.execute(
                    "INSERT INTO sql_run_log (run_id, sql_name, run_status, error_message, date) VALUES "
                    "(%s, %s, %s, %s, %s)", (run_id, sql_file, status, error_msg, datetime.now()))
                self.db.commit()
        except mysql.DatabaseError as error:
            print("ERROR: failed to insert SQL_RUN_LOG: ", error.msg)
            self.exit_program(1)

    def run_sql_files_on_database(self, sql_files):
        """ Find and run relevant SQL files on DB """

        print("Running the following SQL files: ")
        print(*sql_files, sep="\n")
        print("")
        for sql_file in sql_files:
            run_id = int(sql_file.split('.sql')[0].split('_')[-1])
            print(f"Running {sql_file}.. run_id: {run_id}; ", end="")
            with open(f"{self.sqls_dir}/{sql_file}") as sql:
                sql_command = sql.read()
                if not sql_command.replace(";", "").strip():  # file contains no statements
                    print(f"ERROR: failed to run {sql_file}: file contains no statements.")
                    self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file,
                                              status="FAILED", error_msg="ERROR: SQL file contains NO statements.")
                    # return ("ERROR", f"{error.msg}")
                    self.exit_program(1)
                # ayelet print("sql command READ file: ", sql_command)
                for statement in sql_command.split(';'):
                    if not statement.strip():
                        #print(f"statement {statement} empty, continue.")
                        continue
                    else:
                        try:
                            self.cursor.execute(statement)
                        except mysql.DatabaseError as error:
                            print(f"\nERROR: failed to run {sql_file}: ", error.msg)
                            try:
                                self.db.rollback()
                                print(f"   All statements in {sql_file} rolled back.")
                                print("")
                            except mysql.DatabaseError as error:
                                print("\nERROR: failed to rollback: ", error.msg)
                                print("\nHandle manually!")

                            self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="FAILED",
                                                      error_msg=error.msg)
                            self.exit_program(1)
            print("OK.")
            self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="SUCCESS", error_msg="")

