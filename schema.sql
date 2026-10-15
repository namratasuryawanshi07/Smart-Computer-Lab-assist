-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: smart_lab_asset
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `assets`
--

DROP TABLE IF EXISTS `assets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assets` (
  `asset_id` int(11) NOT NULL AUTO_INCREMENT,
  `asset_name` varchar(100) NOT NULL,
  `asset_type` varchar(50) DEFAULT NULL,
  `processor` varchar(100) DEFAULT NULL,
  `ram` varchar(20) DEFAULT NULL,
  `storage` varchar(50) DEFAULT NULL,
  `operating_system` varchar(50) DEFAULT NULL,
  `pc_number` varchar(20) DEFAULT NULL,
  `specifications` varchar(200) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Active',
  `purchase_date` date DEFAULT NULL,
  `added_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`asset_id`),
  KEY `added_by` (`added_by`),
  CONSTRAINT `assets_ibfk_1` FOREIGN KEY (`added_by`) REFERENCES `lab_assistants` (`assistant_id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `complaints`
--

DROP TABLE IF EXISTS `complaints`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `complaints` (
  `complaint_id` int(11) NOT NULL AUTO_INCREMENT,
  `asset_id` int(11) NOT NULL,
  `issue_category` varchar(50) DEFAULT NULL,
  `issue_description` varchar(300) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Open',
  `reported_at` datetime DEFAULT current_timestamp(),
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`complaint_id`),
  KEY `asset_id` (`asset_id`),
  CONSTRAINT `complaints_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`asset_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `faults`
--

DROP TABLE IF EXISTS `faults`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `faults` (
  `fault_id` int(11) NOT NULL AUTO_INCREMENT,
  `asset_id` int(11) NOT NULL,
  `reported_by` int(11) DEFAULT NULL,
  `fault_description` varchar(300) DEFAULT NULL,
  `fault_date` datetime DEFAULT current_timestamp(),
  `severity` varchar(20) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Open',
  PRIMARY KEY (`fault_id`),
  KEY `asset_id` (`asset_id`),
  KEY `reported_by` (`reported_by`),
  CONSTRAINT `faults_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`asset_id`),
  CONSTRAINT `faults_ibfk_2` FOREIGN KEY (`reported_by`) REFERENCES `lab_assistants` (`assistant_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `lab_assistants`
--

DROP TABLE IF EXISTS `lab_assistants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lab_assistants` (
  `assistant_id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`assistant_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `maintenance_history`
--

DROP TABLE IF EXISTS `maintenance_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `maintenance_history` (
  `maintenance_id` int(11) NOT NULL AUTO_INCREMENT,
  `asset_id` int(11) NOT NULL,
  `maintenance_date` datetime DEFAULT current_timestamp(),
  `performed_by` int(11) DEFAULT NULL,
  `remarks` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`maintenance_id`),
  KEY `asset_id` (`asset_id`),
  KEY `performed_by` (`performed_by`),
  CONSTRAINT `maintenance_history_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`asset_id`),
  CONSTRAINT `maintenance_history_ibfk_2` FOREIGN KEY (`performed_by`) REFERENCES `technicians` (`technician_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `repairs`
--

DROP TABLE IF EXISTS `repairs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `repairs` (
  `repair_id` int(11) NOT NULL AUTO_INCREMENT,
  `fault_id` int(11) NOT NULL,
  `technician_id` int(11) DEFAULT NULL,
  `repair_date` datetime DEFAULT current_timestamp(),
  `repair_description` varchar(300) DEFAULT NULL,
  `cost` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`repair_id`),
  KEY `fault_id` (`fault_id`),
  KEY `technician_id` (`technician_id`),
  CONSTRAINT `repairs_ibfk_1` FOREIGN KEY (`fault_id`) REFERENCES `faults` (`fault_id`),
  CONSTRAINT `repairs_ibfk_2` FOREIGN KEY (`technician_id`) REFERENCES `technicians` (`technician_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `technicians`
--

DROP TABLE IF EXISTS `technicians`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `technicians` (
  `technician_id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `contact_number` varchar(20) DEFAULT NULL,
  `specialization` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`technician_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-15 21:20:13
