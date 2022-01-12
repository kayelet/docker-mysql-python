CREATE DATABASE mysql_db;
use mysql_db;

CREATE TABLE IF NOT EXISTS sql_run_log (
  run_id int NOT NULL,
  sql_name varchar(100) NOT NULL,
  run_status varchar(20) NOT NULL,
  error_message varchar(255),
  date datetime NOT NULL,
  PRIMARY KEY (run_id, sql_name, run_status)
) ENGINE=INNODB  DEFAULT CHARSET=utf8;
