CREATE DATABASE `pypress` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
#CREATE USER pypress@localhost IDENTIFIED BY 'pypress';
#grant all privileges on `pypress`.* to pygress@localhost identified by 'pypress';
#grant all privileges on `pypress`.* to pygress@'%' identified by 'pypress';
grant all privileges on pypress.* to fuxi@localhost identified by 'fuxi';
grant all privileges on pypress.* to fuxi@'%' identified by 'fuxi';
flush privileges;
