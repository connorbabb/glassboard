-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`users` (
  `users_id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(45) NOT NULL,
  `password_hash` VARCHAR(45) NOT NULL,
  `date_created` DATETIME NOT NULL,
  PRIMARY KEY (`users_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`sites`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`sites` (
  `sites_id` INT NOT NULL AUTO_INCREMENT,
  `users_id` INT NOT NULL,
  `domain` VARCHAR(255) NOT NULL,
  `api_key` VARCHAR(100) NOT NULL,
  `date_created` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`sites_id`),
  INDEX `fk_sites_users_idx` (`users_id` ASC) VISIBLE,
  CONSTRAINT `fk_sites_users`
    FOREIGN KEY (`users_id`)
    REFERENCES `mydb`.`users` (`users_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`events`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`events` (
  `events_id` INT NOT NULL AUTO_INCREMENT,
  `sites_id` INT NOT NULL,
  `page` VARCHAR(255) NULL,
  `element` VARCHAR(255) NULL,
  `event_type` VARCHAR(45) NULL,
  `timestamp` DATETIME NOT NULL,
  `session_id` VARCHAR(100) NULL,
  PRIMARY KEY (`events_id`),
  INDEX `fk_events_sites1_idx` (`sites_id` ASC) VISIBLE,
  CONSTRAINT `fk_events_sites1`
    FOREIGN KEY (`sites_id`)
    REFERENCES `mydb`.`sites` (`sites_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
