# UTF-8

# docker exec -ti 83dd95de0a0c python main.py
from database import Database
import sys
from cryptography.fernet import Fernet


def main():
    sqls_dir = "/tmp"
    i_sql = None

    if len(sys.argv) > 2:
        print("ERROR: wrong number of arguments.")
        print("Usage: ")
        print("    python main.py [SQL script|SQL dir]")
        exit(1)
    if len(sys.argv) == 2:
        i_sql = sys.argv[1]
        sqls_dir = ""

    database = "mysql_db"
    host = "db"
    port = "3306"
    db_user = "root"
    db_user_password = "root"
    sqls_dir = sqls_dir

    user = Database(database=database, host=host, port=port, user=db_user, password=db_user_password, sqls_dir=sqls_dir)

    last_script_id_tup = user.get_last_run_script_id()
    sql_files = user.generate_scripts_list(last_script_id_tup, i_sqls=i_sql)
    if not sql_files:
        print(f"No new SQL files with RUN_ID higher than {last_script_id_tup[0]} are found.")
        user.exit_program(0)

    user.run_sql_files_on_database(sql_files)
    user.exit_program(0)


if __name__ == "__main__":
    main()