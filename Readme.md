# JCSQL plugin for SQL for Sublime text

## Plugin allows executing SQL queries using DB connections
Now available:
 - Oracle DB
 - Cloudera Impala

## Install:

Assume, that Sublime text editor has already installed.

1) Install Python 3.6+ (https://www.python.org/)
2) Install numpy, pyodbc
```
pip install numpy pyodbc
```
3) Download sqlplus + oracle instant client (https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html)
4) Install and configure cloudera ODBC driver (https://www.cloudera.com -> Downloads -> Database Drivers)
5) Add sqlplus, python to Path env varaible

6) Copy folder JCSQL to (for win) c:~\AppData\Roaming\Sublime Text 3\Packages\
7) Relaunch Sublime text

Add Connection:

 - [ctrl+shift+p] -> JCQL:Add new connection:
```
{
      "connection_name": "CONNECTION_NAME_HERE"
    , "environment": "ENVIRONMENT_HERE(oracle/impala)"
    , "connection_string": "CONNECTION_STRING_HERE"
}
```

Use it to execute a code
 - [ctrl+shift+enter] -> {conenction name}
----

### Supported commands :
 - Add connection
 - Modify connection
 - Delete connection
 - Run code*
 - Run code in {connection_name}
 - Run explain in {connection_name}

*for "Run code in" last used connection saved automatically and goes to "Run code"

### Help commands:
 - Close without saving [ctrl+q]
 - Fetch all (table view)
 - Save to csv (csv view)

### Main biddings:
 - [ctrl+enter] / [f5] - Run Code
 - [ctrl+shift+enter] - Run Code in
 - [f10] - Run explain in

For DML and explain commands for oracle plugin uses oracle "sqlplus", so it needs to be configured
For impala queries, the ODBC driver should be configured
The plugin uses python as an external application to execute queries, so it should be available like 'python' from cmd

### Features:
 - Work from sublime text editor as a single environment
 - Non blocking parallel query execution
 - Query history + query result history
 - Convert result to csv <-> table view
 - Result to virtual view -> easy save to file
 - Fetch rows by request / fetch all rows

Examples:

Oracle query:
```
select 1 as id from dual union all
select 2500 as id from dual;
```
Result:

```
[2020-01-13 15:46:59] Connected to oracle

select 1 as id from dual union all
select 2500 as id from dual

+------+
| id   |
+------+
| 1    |
| 2500 |
+------+

Fetched 2 rows

Elapsed 0:00:00.018945 s

Fetched all rows.
```

Cloudera Impala query:
```
select 'lol test_string' as value union all
select 'test string 2 for test' as value
```
Result:
```
[2020-01-13 15:44:41] Connected to impala

select 'lol test_string' as value union all
select 'test string 2 for test' as value

+------------------------+
| value                  |
+------------------------+
| lol test_string        |
| test string 2 for test |
+------------------------+

Fetched 2 rows

Elapsed 0:00:00.062832 s

Fetched all rows.
```

Oracle explain:
```
Session altered.

SQL> EXPLAIN PLAN FOR
  2  select 1 as id from dual union all
  3  select 2 as id from dual;

Explained.

Elapsed: 00:00:00.05
SQL> SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
Plan hash value: 3964740403

-----------------------------------------------------------------
| Id  | Operation        | Name | Rows  | Cost (%CPU)| Time     |
-----------------------------------------------------------------
|   0 | SELECT STATEMENT |      |     2 |     4   (0)| 00:00:01 |
|   1 |  UNION-ALL       |      |       |            |          |
|   2 |   FAST DUAL      |      |     1 |     2   (0)| 00:00:01 |
|   3 |   FAST DUAL      |      |     1 |     2   (0)| 00:00:01 |
-----------------------------------------------------------------

10 rows selected.

Elapsed: 00:00:00.10
```

Impala Explain:
```
[2020-01-13 15:45:47] Connected to impala

EXPLAIN
select 'lol test_string' as value union all
select 'test string 2 for test' as value

+----------------------------------------------+
| explain string                               |
+----------------------------------------------+
| Max Per-Host Resource Reservation: Memory=0B |
| Per-Host Resource Estimates: Memory=10.00MB  |
| Codegen disabled by planner                  |
|                                              |
| PLAN-ROOT SINK                               |
| |                                            |
| 00:UNION                                     |
|    constant-operands=2                       |
+----------------------------------------------+

Fetched 8 rows

Elapsed 0:00:00.057832 s

Fetched all rows.
```