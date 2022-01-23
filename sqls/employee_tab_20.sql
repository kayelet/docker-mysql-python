CREATE TABLE IF NOT EXISTS EMPLOYEE
(
  emp_id int(4) NOT NULL PRIMARY KEY,
  first_name varchar(30) NOT NULL,
  last_name varchar(30) NOT NULL,
  dept_id int(4) NOT NULL,
  FOREIGN KEY (dept_id)
        REFERENCES DEPARTMENT(dept_id)
        ON DELETE CASCADE
) ENGINE=INNODB DEFAULT CHARSET=utf8;

