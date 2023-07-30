CREATE TABLE `avatarfriends` (
  `friendId1` int(32) NOT NULL,
  `friendId2` int(32) NOT NULL,
  `openChatYesNo` tinyint(1) NOT NULL default '0',
  PRIMARY KEY  (`friendId1`,`friendId2`),
  KEY `idxFriend1` (`friendId1`),
  KEY `idxFriend2` (`friendId2`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

