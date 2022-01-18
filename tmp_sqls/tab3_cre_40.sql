CREATE TABLE IF NOT EXISTS tab3 (
  emp_id int NOT NULL AUTO_INCREMENT,
  first_name varchar(20) NOT NULL,
  last_name varchar(20) NOT NULL,
  dept_id tinyint NOT NULL,
  dept_name varchar(255) NOT NULL,
  dept_num_of_emps int DEFAULT '0',
  PRIMARY KEY (emp_id),
  FOREIGN KEY (dept_id) REFERENCES tab1(dept_id)
) ENGINE=INNODB  DEFAULT CHARSET=latin1 ;