# UTF-8

# docker exec -ti 83dd95de0a0c python main.py

from database import Database
import sys


def main():
    # database = os.environ.get('MYSQL_DATABASE')
    # host = os.environ.get('MYSQL_HOST')
    # db_user = os.environ.get('MYSQL_USER')
    # db_user_password = os.environ.get('MYSQL_PASSWORD')
    # sqls_dir = os.environ.get('SQLS_DIR',default='/tmp')
    # user = Database(database=database, host=host, user=db_user, password=db_user_password, sqls_dir=sqls_dir)

    database = "mysql_db"
    host = "db"
    port = "3606"
    db_user = "root"
    db_user_password = "root"
    sqls_dir = "/tmp"
    # mysql -h <IP provided by inspect command> -P <port> -u <user> -p <db name>
    user = Database(database=database, host=host, port=port, user=db_user, password=db_user_password, sqls_dir=sqls_dir)
    i_sql = None
    #last_run_script_id = user.get_last_run_script_id()
    #scripts_list = user.generate_scripts_list(last_run_script_id)
    #if not scripts_list:
    #    print(f"Nothing to run on user {db_user}.")
    #    user.exit_program(0)

    print("len is ", len(sys.argv))
    print('Argument List:', str(sys.argv))
    print('Argument List no str:', sys.argv)

    if len(sys.argv) > 2:
        print("ERROR: wrong number of arguments.")
        print("Usage: ")
        print("    python main.py [SQL script|SQL dir]")
        user.exit_program(1)
    if len(sys.argv) == 2:
        i_sql = sys.argv[1]




    last_script_id_tup = user.get_last_run_script_id()
    sql_files = user.generate_scripts_list(last_script_id_tup, i_sqls=i_sql)
    if not sql_files:
        # return "{Status: nothing to run.}"
        print(f"No new SQL files with RUN_ID higher than {last_script_id_tup[0]} are found.")
        user.exit_program(0)

    user.run_sql_files_on_database(sql_files)
    user.exit_program(0)


if __name__ == "__main__":
    main()