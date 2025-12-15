# Shared Templates

## Structure
- `common/` - SQL databases (MySQL, PostgreSQL, MSSQL, ClickHouse)
- `mongo/` - MongoDB applications

## Usage
Templates in sample apps are symlinks to shared templates here.

## Modifying Templates
Edit files in this directory - changes apply to all apps using them.

## Apps Using Shared Templates
**Common (SQL)**: flask-*, fastapi-*, starlette-*, quart-* apps
**Mongo**: flask-mongo, quart-mongo

## Quick Checks
```bash
# Verify symlinks work
cat sample-apps/flask-mysql/templates/index.html

# Find all symlinks
find sample-apps -name "*.html" -type l
```