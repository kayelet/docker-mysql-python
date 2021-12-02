CREATE TABLE IF NOT EXISTS tab1 (
  dept_id tinyint NOT NULL,
  dept_name varchar(255) NOT NULL,
  dept_num_of_emps int NOT NULL DEFAULT 0,
  PRIMARY KEY (dept_id)
) ENGINE=INNODB  DEFAULT CHARSET='latin1' ;
