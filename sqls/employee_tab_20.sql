CREATE TABLE IF NOT EXISTS EMPLOYEE (
  emp_id tinyint NOT NULL,
  first_name varchar(30) NOT NULL,
  last_name varchar(30) NOT NULL,
  dept_id tinyint NOT NULL,
  PRIMARY KEY (emp_id),
  FOREIGN KEY (dept_id)
        REFERENCES department(dept_id)
        ON DELETE CASCADE
) ENGINE=INNODB  DEFAULT CHARSET='latin1' ;

