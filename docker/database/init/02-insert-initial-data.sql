-- Insert initial data for Haystack system
USE Peregrin;

-- Insert default link types
INSERT IGNORE INTO `LinkTypes` (`LinkTypeName`, `LinkTypeDesc`) VALUES
('contains', 'Parent item contains child item'),
('references', 'Item references another item'),
('download', 'Item was downloaded from source'),
('duplicate', 'Item is a duplicate of another'),
('related', 'Items are related but not hierarchical');

-- Insert default actions
INSERT IGNORE INTO `Actions` (`actionName`, `actionDesc`) VALUES
('WebCrawler', 'Web crawling and page discovery'),
('ParseContents', 'Content parsing and extraction'),
('FileCrawler', 'File system crawling'),
('extractor', 'Data extraction from files'),
('downloader', 'File downloading'),
('config', 'Configuration management'),
('Status', 'System status reporting');

-- Insert default configuration values
INSERT IGNORE INTO `Config` (`configName`, `configValue`) VALUES
('RunQueue', '1'),
('MaxConcurrentJobs', '5'),
('DefaultDelay', '5'),
('SystemVersion', '1.0'),
('LastMaintenance', NOW());

-- Create initial system engine entry
INSERT IGNORE INTO `Engines` (`EngineName`, `EngineVersion`, `EngineDesc`) VALUES
('SystemEngine', '1.0', 'Core system engine for administrative tasks');