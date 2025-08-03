-- Haystack Database Schema Creation Script
-- This creates the core tables for the Peregrin/Haystack system

USE Peregrin;

-- Create Engines table
CREATE TABLE IF NOT EXISTS `Engines` (
  `EngineId` int(11) NOT NULL AUTO_INCREMENT,
  `EngineName` varchar(100) NOT NULL,
  `EngineVersion` varchar(20) NOT NULL,
  `EngineDesc` text,
  `EngineDisabled` tinyint(1) DEFAULT 0,
  `EngineCreated` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`EngineId`),
  UNIQUE KEY `unique_engine` (`EngineName`, `EngineVersion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create Actions table
CREATE TABLE IF NOT EXISTS `Actions` (
  `actionId` int(11) NOT NULL AUTO_INCREMENT,
  `actionName` varchar(100) NOT NULL,
  `actionDesc` text,
  `actionCreated` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`actionId`),
  UNIQUE KEY `unique_action` (`actionName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create EngineActions table
CREATE TABLE IF NOT EXISTS `EngineActions` (
  `engineActionId` int(11) NOT NULL AUTO_INCREMENT,
  `engineId` int(11) NOT NULL,
  `actionId` int(11) NOT NULL,
  `actionFunction` varchar(100) NOT NULL,
  `actionParams` text,
  `engineActionDisabled` tinyint(1) DEFAULT 0,
  `engineActionCreated` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`engineActionId`),
  KEY `fk_engineactions_engine` (`engineId`),
  KEY `fk_engineactions_action` (`actionId`),
  CONSTRAINT `fk_engineactions_engine` FOREIGN KEY (`engineId`) REFERENCES `Engines` (`EngineId`),
  CONSTRAINT `fk_engineactions_action` FOREIGN KEY (`actionId`) REFERENCES `Actions` (`actionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create Items table
CREATE TABLE IF NOT EXISTS `Items` (
  `itemId` int(11) NOT NULL AUTO_INCREMENT,
  `ItemURI` text NOT NULL,
  `EngineId` int(11) NOT NULL,
  `ItemDTS` timestamp NOT NULL,
  `itemCreated` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`itemId`),
  KEY `fk_items_engine` (`EngineId`),
  KEY `idx_items_uri` (`ItemURI`(255)),
  KEY `idx_items_date` (`ItemDTS`),
  CONSTRAINT `fk_items_engine` FOREIGN KEY (`EngineId`) REFERENCES `Engines` (`EngineId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create ItemData table
CREATE TABLE IF NOT EXISTS `ItemData` (
  `ItemDataId` int(11) NOT NULL AUTO_INCREMENT,
  `itemId` int(11) NOT NULL,
  `itemData` varchar(100) NOT NULL,
  `itemDataValue` text,
  `itemDataSeq` int(11) DEFAULT 0,
  `itemDataAdded` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ItemDataId`),
  KEY `fk_itemdata_item` (`itemId`),
  KEY `idx_itemdata_type` (`itemData`),
  KEY `idx_itemdata_seq` (`itemDataSeq`),
  CONSTRAINT `fk_itemdata_item` FOREIGN KEY (`itemId`) REFERENCES `Items` (`itemId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create ItemEvents table
CREATE TABLE IF NOT EXISTS `ItemEvents` (
  `ItemEventId` int(11) NOT NULL AUTO_INCREMENT,
  `engineId` int(11) NOT NULL,
  `actionId` int(11) NOT NULL,
  `itemId` int(11) NOT NULL,
  `itemEventAddedDate` timestamp DEFAULT CURRENT_TIMESTAMP,
  `itemEventDate` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`ItemEventId`),
  KEY `fk_itemevents_engine` (`engineId`),
  KEY `fk_itemevents_action` (`actionId`),
  KEY `fk_itemevents_item` (`itemId`),
  KEY `idx_itemevents_status` (`itemEventDate`),
  CONSTRAINT `fk_itemevents_engine` FOREIGN KEY (`engineId`) REFERENCES `Engines` (`EngineId`),
  CONSTRAINT `fk_itemevents_action` FOREIGN KEY (`actionId`) REFERENCES `Actions` (`actionId`),
  CONSTRAINT `fk_itemevents_item` FOREIGN KEY (`itemId`) REFERENCES `Items` (`itemId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create LinkTypes table
CREATE TABLE IF NOT EXISTS `LinkTypes` (
  `LinkTypeId` int(11) NOT NULL AUTO_INCREMENT,
  `LinkTypeName` varchar(50) NOT NULL,
  `LinkTypeDesc` text,
  PRIMARY KEY (`LinkTypeId`),
  UNIQUE KEY `unique_linktype` (`LinkTypeName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create ItemLinks table
CREATE TABLE IF NOT EXISTS `ItemLinks` (
  `itemLinkId` int(11) NOT NULL AUTO_INCREMENT,
  `EngineId` int(11) NOT NULL,
  `itemId_left` int(11) NOT NULL,
  `itemId_right` int(11) NOT NULL,
  `linkTypeId` int(11) NOT NULL,
  `itemLinkDTS` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`itemLinkId`),
  KEY `fk_itemlinks_engine` (`EngineId`),
  KEY `fk_itemlinks_left` (`itemId_left`),
  KEY `fk_itemlinks_right` (`itemId_right`),
  KEY `fk_itemlinks_linktype` (`linkTypeId`),
  CONSTRAINT `fk_itemlinks_engine` FOREIGN KEY (`EngineId`) REFERENCES `Engines` (`EngineId`),
  CONSTRAINT `fk_itemlinks_left` FOREIGN KEY (`itemId_left`) REFERENCES `Items` (`itemId`),
  CONSTRAINT `fk_itemlinks_right` FOREIGN KEY (`itemId_right`) REFERENCES `Items` (`itemId`),
  CONSTRAINT `fk_itemlinks_linktype` FOREIGN KEY (`linkTypeId`) REFERENCES `LinkTypes` (`LinkTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create Status table
CREATE TABLE IF NOT EXISTS `Status` (
  `statusId` int(11) NOT NULL AUTO_INCREMENT,
  `engineId` int(11) NOT NULL,
  `actionId` int(11) NOT NULL,
  `StatusMessage` text,
  `StatusDate` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`statusId`),
  KEY `fk_status_engine` (`engineId`),
  KEY `fk_status_action` (`actionId`),
  KEY `idx_status_date` (`StatusDate`),
  CONSTRAINT `fk_status_engine` FOREIGN KEY (`engineId`) REFERENCES `Engines` (`EngineId`),
  CONSTRAINT `fk_status_action` FOREIGN KEY (`actionId`) REFERENCES `Actions` (`actionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create Config table
CREATE TABLE IF NOT EXISTS `Config` (
  `configId` int(11) NOT NULL AUTO_INCREMENT,
  `configName` varchar(100) NOT NULL,
  `configValue` text,
  `configUpdated` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`configId`),
  UNIQUE KEY `unique_config` (`configName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;