### Timesheet reports 
Commulative timesheet report from Sugar and JIRA with publishing to Google Docs 
### Running with Python
Designed for Python 2.7 
```python 
$ pip27 install -i requirements.txt
$ python27 runthread.py
```
### Confuguration options
Configuration can be done through `.env` file or enviroment variables
###### Common for all payloads:
- `RUN_INTERVAL` - Running interval in seconds (default 300)
- `DEBUG` - (True, False)
- `DB_ENGINE` - Database engine (postgres | mysql) 
- `DATABASE_URL` - Database URL in [engine]://[user]:[pass]@[host]:[port]/[db]. Alternativetly credentials can be specified separately
###### MySQL specific:
- `MYSQL_USER` - MySQL user (string)
- `MYSQL_PASS` - MySQL password (string)
- `MYSQL_HOST` - MySQL host (string)
- `MYSQL_DB` - MySQL database (string)
- `MYSQL_PORT` - MySQL Port (int, default 3306)
###### Posgres specific:
- `PG_USER` - Postgres user (string)
- `PG_PASS` - Postgres password (string)
- `PG_HOST` - Postgres host (string)
- `PG_DB` - Postgres database (string)
- `PG_PORT` - Postgres Port (int, default 3306)
###### SugarCRM specific:
- `SUGAR_USER` - SugarCRM user name
- `SUGAR_PASS` - SugarCRM path
- `SUGAR_REST` - Rest service v4_1 ONLY(!)
###### JIRA specific:
- `JIRA_USER` - Jira user name
- `JIRA_PASS` - Jira password
- `JIRA_URL` - HTTPS URL to JIRA main site (no rest suffix is required)
- `JIRA_THREADS` - Number of threads to download data with
###### Google specific:
GOOGLE_SHEET - Google spreadsheet ID (can be copied form URL something like *0Av6KMa_AP8_sdDdXXDgzbP45V0laamdfa0N2WFc0R1E*)
### Running with Heroku
Able to run using Free Heroku profile. Please refer to Heroku [guide](https://devcenter.heroku.com/articles/getting-started-with-python)
