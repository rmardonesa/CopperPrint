IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'copperprint_oltp')
    CREATE DATABASE copperprint_oltp;
GO

USE copperprint_oltp;
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'cp')
    EXEC('CREATE SCHEMA cp');
GO
