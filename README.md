# docker-python-flask
python-flask project based on docker config. The project was created as path of self-learning and practicing Docker principles.
The configuration consists on two containers:
1. Mysql container. Already contains DATABASE mysql_db and SQL log table SQL_RUN_LOG.
2. Applicative python container, also allows to send requests to query/act on the SQLs scripts/tables via the Flask app.

# OS
This docker cluster has been written and run on Windows 10.

# project's structure
app/  
  - main.py: runs SQL files on the MYSQL database   
  - app.py: runs the Flask app  
  - database.py: contains the Database class with properties and methods run by the main.py script  
  - Dockerfile: builds the mysql_flask_app container  
  - requirements: contains list of Python required libraries  
  - templates/  
    - index.html  

db/  
  - init.sql: initializes the mysql_db container by creating database 'mysql_db' and creating SQL_RUN_LOG table.  

sqls/   
  - sql_run_log_0.sql: in case table is dropped, this file creating it will be the first to run by main.py  
  - department_tab_10.sql: example file  
  - employee_tab_20.sql: example file  
  - department_ins_30.sql: example file  

docker-compose.yml: creates the docker cluster with the two containers  
  

# Python-Mysql development Platform
## Purpose
The project provides dev cluster allowing the user to run SQL scripts on the (Mysql) database and develop/test/run against it in Python environment.
The run SQL files are registered in table SQL_RUN_LOG.

### SQL scripts
1. Although the table created already in image, the script for creating log table SQL_RUN_LOG already provided unders sqls: sql_run_log_0.sql
   DO not change the RUN_ID (0) of script, it makes it the first to be run, before any other SQL file.
2. The SQL file names must comply with name convention [a-zA-Z_]+_[0-9]+.sql
   Although table/object name is not encorced, it is recommended to create file names with the name of the object and its type.
   Example: employee_tab_10.sql
3. The number at the end of the file name represents the order in which the files should be run.  
4. This number is referred to as the SQL RUN_ID and written as such in the SQL_RUN_LOG table.
5. Recommendation: create the SQL files with a gap of 10 between consecutive files. For example, department_tab_10.sql, employee_tab_20.sql etc; this
   will allow you flexibility in filling unnoticed data gaps without having to change all scripts names if some scripts were forgotten.
6. The gaps between SQL RUN_ID, though, must not exceed 10. For example, running department_tab_10.sql, employee_tab_21.sql with no SQL script with RUN_ID between 10 and 21,
   will issue an error.
7. Two SQL files cannot have the same RUN_ID. If found, an error will be issued.   

## Setup and run the Docker cluster
(Docker-desktop installtion assumed)
1. clone this repository to you directory path on your OS.
2. go to the local/repository/path
3. run docker-compose up

You should now see the cluster via your docker-desktop
![Imgur Image](docker_mysql_python_cluster.png)

### SQLs run flow
1. Docker container cluster must be up and running when running the SQL files.
When running Python script main.py, the run flow is as follows:
2. If table SQL_RUN_LOG does not exist, it will be created by running provided script sql_run_log_0.sql
3. A record with SQL file name, its RUN_ID, status (SUCCESS or FAILURE), error (in case of FAILURE) and date are written after the run of each SQL file.
4. The SQL files are run according to the last RUN_ID found in SQL_RUN_LOG table with status SUCCESS.
   example A: if scripts department_tab_10.sql, employee_tab_20.sql and department_tab_10.sql, employee_tab_20.sql passed successfully while 
   employee_ins_30.sql failed, the next time main.py will run, the first SQL file to run with be with the smallest RUN_ID that is greater than 20.
5. The main.py script will exit with error at the first FAILURE. Before exiting, a ROLLBACK will be executed for all file's statements.  
   Note: rollback can be applied only for DML statements.

## How to run the program
* From container (from /app): python main.py  
* From terminal: docker exec -ti mysql_flask_app python main.py  
* To run a specific SQL: docker exec -ti mysql_flask_app python main.py \<SQL file\>  
* To run SQLs from a directory: docker exec -ti mysql_flask_app python main.py \<path to SQLs directory\>
** Note: SQLs default path is /tmp  
   if running SQL/s from a different location in container, it must be specified.  
  
## Examples
#### from container
![Imgur Image](run_from_container_success_ex1.png)
#### from terminal
![Imgur Image](run_from_terminal_success_ex2.png)
### output when no files with RUN_ID higher than in SQL_RUN_LOG table found in sql files
![Imgur Image](run_from_terminal_no_files_to_run_ex3.png)

 
## View Database on Mysql Client UI
For a better view of your DB tables and run status in SQL_RUN_LOG table, configure DB on one of the Mysql available UIs.
Example, MySql Workbench:
![Imgur Image](config_mysql_workbench.png) 
  
## SQL_RUN_LOG view
![Imgur Image](mysql_workbench_sql_run_log_v1.png)

## Operations available via Flask URL End-Points
Recommended: use one of the available API platform on the internet to view/act on the available flask end-points as specified in the Flask base URL.  
Example: Postman  
You can view the available end-points on the base Flask URL, as follows:
![Imgur Image](python_mysql_flask_home.png)

## Examples
### Getting the data of all SQL files that ran successfully
![Imgur Image](postman_success.png)
### Getting info of a specific SQL but its RUN_ID
![Imgur Image](postman_run_id.png)
### Delete tables and truncate SQL_RUN_LOG
You can achieve the above by entring end-point "drop_tables", BUT you have to set a header key first.
In this project the key hasn't been encrypted. 
Key-name: Api-Key-Test, Value: ayelet
Configure the above in the api platform you're using under Headers. If not confgured you'll get a "Not Authorized" response.
![Imgur Image](postman_drop_tables.png)


