CREATE TABLE `entities` (
  `id` char(32) NOT NULL DEFAULT '',
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `body` mediumblob NOT NULL,
  `auto_increment` int(11) NOT NULL AUTO_INCREMENT COMMENT 'basicly never used',
  PRIMARY KEY (`auto_increment`),
  UNIQUE KEY `id` (`id`),
  KEY `updated` (`updated`)
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=utf8;