#!/usr/bin/env bash
# Wait for database to startup 
sleep 20
./opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Strong!Passw0rd" -i setup.sql -N -C
