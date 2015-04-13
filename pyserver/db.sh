CREATE DATABASE `pypress` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
CREATE USER app@localhost IDENTIFIED BY 'app';
grant all privileges on pypress.* to app@localhost identified by 'app';
grant all privileges on pypress.* to app@'%' identified by 'app';
#grant all privileges on pypress.* to fuxi@localhost identified by 'fuxi';
#grant all privileges on pypress.* to fuxi@'%' identified by 'fuxi';
flush privileges;
