-- Check if the database exists
IF NOT EXISTS (
    SELECT name 
    FROM sys.databases 
    WHERE name = 'db'
)
BEGIN
    -- Create the database if it does not exist
    CREATE DATABASE db;
END
GO

-- Use the database
USE db;
GO

-- Drop the table if it exists
IF OBJECT_ID('dbo.dogs', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.dogs;
END
GO

-- Create the table if it does not exist
CREATE TABLE dbo.dogs (
    id INT IDENTITY(1,1) PRIMARY KEY,  -- Use IDENTITY for auto-increment
    dog_name NVARCHAR(250) NOT NULL,   -- Use NVARCHAR for string types
    isAdmin BIT NOT NULL DEFAULT 0      -- Use BIT for boolean types
);
GO
