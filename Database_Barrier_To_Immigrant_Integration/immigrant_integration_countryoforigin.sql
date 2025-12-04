-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: immigrant_integration
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `countryoforigin`
--

DROP TABLE IF EXISTS `countryoforigin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `countryoforigin` (
  `country_id` int NOT NULL AUTO_INCREMENT,
  `country_name` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `population_migrants` int DEFAULT NULL,
  `major_language` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`country_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `countryoforigin`
--

LOCK TABLES `countryoforigin` WRITE;
/*!40000 ALTER TABLE `countryoforigin` DISABLE KEYS */;
INSERT INTO `countryoforigin` VALUES (1,'Mexico','North America',23000,'Spanish'),(2,'El Salvador','Central America',12000,'Spanish'),(3,'Honduras','Central America',11000,'Spanish'),(4,'Guatemala','Central America',9500,'Spanish'),(5,'Venezuela','South America',2100,'Spanish'),(6,'Colombia','South America',1500,'Spanish'),(7,'Cuba','Caribbean',800,'Spanish'),(8,'Haiti','Caribbean',300,'Haitian Creole'),(9,'Brazil','South America',600,'Portuguese'),(10,'India','Asia',600,'Hindi'),(11,'Nigeria','Africa',500,'English'),(12,'China','Asia',450,'Mandarin'),(13,'Somalia','Africa',200,'Somali'),(14,'Ethiopia','Africa',180,'Amharic'),(15,'Ukraine','Europe',100,'Ukrainian'),(16,'Dominican Republic','Caribbean',1100,'Spanish'),(17,'Philippines','Southeast Asia',210,'Filipino'),(18,'Vietnam','Southeast Asia',1400,'Vietnamese'),(19,'Afghanistan','South Asia',60,'Dari'),(20,'Russia','Eastern Europe',400,'Russian');
/*!40000 ALTER TABLE `countryoforigin` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-01 15:18:06
