CREATE TABLE `index_login` (
  `login` varchar(100) NOT NULL,
  `entity_id` char(32) NOT NULL,
  PRIMARY KEY (`login`,`entity_id`),
  UNIQUE KEY `entity_id` (`entity_id`),
  UNIQUE KEY `login` (`login`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;