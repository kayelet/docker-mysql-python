CREATE TABLE IF NOT EXISTS `tab2` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `password` varchar(50) NOT NULL,
  `status` tinyint(10) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=INNODB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=10001 ;
