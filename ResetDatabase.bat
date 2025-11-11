@echo off
REM Database Reset Script for Windows
REM Drops and recreates the database with fresh schema

echo ========================================
echo DATABASE RESET SCRIPT
echo ========================================
echo.
echo WARNING: This will DELETE ALL DATA in the database!
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Connecting to PostgreSQL...
echo.

REM Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS multi_agent_ecommerce;"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to drop database!
    echo.
    echo Possible reasons:
    echo 1. PostgreSQL not running
    echo 2. Wrong credentials
    echo 3. Database in use (close all connections)
    echo.
    pause
    exit /b 1
)

echo Database dropped successfully.
echo.

psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to create database!
    pause
    exit /b 1
)

echo Database created successfully.
echo.

echo ========================================
echo SUCCESS! Database reset complete.
echo ========================================
echo.
echo Next steps:
echo 1. Run: InitDatabase.bat (create tables)
echo 2. Run: SeedDatabase.bat (populate data)
echo.
pause
