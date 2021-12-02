import mysql.connector as mysql
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
        last_id = 0
        self.cursor.execute("SHOW TABLES LIKE 'sql_run_log'")
        if len(self.cursor.fetchall()) == 0:
            self.create_log_table()
        self.cursor.execute("select max(run_id) from sql_run_log where run_status='SUCCESS'")
        res = self.cursor.fetchall()[0][0]
        if res is not None:
            last_id = res
        return last_id

    def verify_scripts_run_id_uniqueness(self, files_list):
        """ Verify each SQL file has a unique ID """
        run_id_counts = Counter([script.split('.sql')[0].split('_')[-1] for script in files_list])
        duplicate_run_ids = [(key, value) for key, value in dict(run_id_counts).items() if value > 1]
        if duplicate_run_ids:
            print("ERROR: Duplicate RUN_IDs found as follows:")
            for dup_ext in duplicate_run_ids:
                print(f"   Extension _{dup_ext[0]}.sql found in {dup_ext[1]} SQL scripts.")
            self.exit_program(1)

    def verify_valid_run_id_gaps(self, files_list):
        run_id_list = [int(num.split('.sql')[0].split('_')[-1]) for num in files_list]
        # print(run_id_list)
        run_id_gaps = [j - i for i, j in zip(run_id_list[:-1], run_id_list[1:])]
        wide_run_id_tups = [(files_list[i], files_list[i+1]) for i, gap in enumerate(run_id_gaps) if gap > 10]
        if wide_run_id_tups:
            print("The following SQL files have to wide RUN_ID gaps (maximum of 10 is allowed):")
            print(wide_run_id_tups, sep="\n")
            self.exit_program(1)
        # print(files_list)
        # print(run_id_gaps)
        # exit(0)

    def generate_scripts_list(self, last_script_id):
        """ Generate the list of the SQL files that should run
            on database. SQL files must comply with name pattern
        """
        regex = re.compile(".+_[0-9]+\.sql$")
        sql_files = [ file for file in os.listdir(self.sqls_dir) if regex.match(file) and
                       int(str(file).split('.sql')[0].split('_')[-1]) > last_script_id ]

        sql_files.sort(key=lambda sql_file: int(str(sql_file).split('.sql')[0].split('_')[-1]))
        self.verify_scripts_run_id_uniqueness(sql_files)
        self.verify_valid_run_id_gaps(sql_files)
        return sql_files

    def write_to_sql_run_log(self, run_id:int, sql_file:str, status:str, error_msg:str):
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

    def run_sql_files_on_database(self):
        """ Find and run relevant SQL files on DB """
        last_script_id = self.get_last_run_script_id()
        sql_files = self.generate_scripts_list(last_script_id)
        if not sql_files:
            print("Nothing to run.")
            self.exit_program(0)

        print("Running the following SQL files: ")
        print(*sql_files, sep="\n")
        print("")
        for sql_file in sql_files:
            run_id = sql_file.split('.sql')[0].split('_')[-1]
            with open(f"{self.sqls_dir}/{sql_file}") as sql:
                sql_command = sql.read()
                for statement in sql_command.split(';')[:-1]:
                    try:
                        print(f"Running {sql_file}.. run_id: {run_id}; ", end="")
                        self.cursor.execute(statement)
                        print("OK.")
                    except mysql.DatabaseError as error:
                        print(f"\nERROR: failed to run {sql_file}: ", error.msg)
                        try:
                            self.db.rollback()
                            print(f"   All statements in {sql_file} rolled back.")
                            print("")
                        except mysql.DatabaseError as error:
                            print("\nERROR: failed to rollback: ", error.msg )
                            print("\nHandle manually!")

                        self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="FAILED", error_msg=error.msg)
                        self.exit_program(1)
                else:
                    self.write_to_sql_run_log(run_id=run_id, sql_file=sql_file, status="SUCCESS", error_msg="")

