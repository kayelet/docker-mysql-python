
from database import Database
import os


def main():
    # database = os.environ.get('MYSQL_DATABASE')
    # host = os.environ.get('MYSQL_HOST')
    # db_user = os.environ.get('MYSQL_USER')
    # db_user_password = os.environ.get('MYSQL_PASSWORD')
    # sqls_dir = os.environ.get('SQLS_DIR',default='/tmp')
    # user = Database(database=database, host=host, user=db_user, password=db_user_password, sqls_dir=sqls_dir)

    database = "mysql_db"
    host = "db"
    port = "3306"
    db_user = "root"
    db_user_password = "root"
    sqls_dir = "/tmp"
    user = Database(database=database, host=host, port=port, user=db_user, password=db_user_password, sqls_dir=sqls_dir)

    last_run_script_id = user.get_last_run_script_id()
    scripts_list = user.generate_scripts_list(last_run_script_id)
    if not scripts_list:
        print(f"Nothing to run on user {db_user}.")
        user.exit_program(0)
    user.run_sql_files_on_database()
    user.exit_program(0)


if __name__ == "__main__":
    main()