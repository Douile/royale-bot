# Royale Bot _Personal_
[![CodeFactor](https://www.codefactor.io/repository/github/douile/royale-bot/badge/personal)](https://www.codefactor.io/repository/github/douile/royale-bot/overview/personal)

RoyaleBot is a fortnite discord bot that allows users to view their ingame stats, the current shop and in game news.

The following is a guide on how to install and run RoyaleBot in your own enviroment

## Requirements
To run RoyaleBot you need python 3.6 and a postgresql database.

### Local setup
#### Getting the files
Clone this repository into your desired directory using `git clone --single-branch --branch personal https://github.com/Douile/royale-bot.git`.
####  Setting up the database
You can set up the database on the same machine as you run the bot, download the postgres installer [here](https://www.postgresql.org/download/). After setting up the server you should have a username and password (be sure to ensure the server is always running). You must then initialize your database by running (in directory you cloned into) `psql -h localhost -d {YOUR DATABASE NAME} -u {YOUR DATABASE USERNAME} -p {YOUR DATABASE PORT} -f ./create_schema.sql`. You must then format the connection string into a postgresql connection URL ([docs](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)), e.g. `postgres://user:password@localhost:port/database`.

##### _Notes_

The default username when you create the postgres database is `postgres`.
#### Running
##### Windows
Before you run you must modify the `start.template.bat` file, modify lines 9-16 with your respective values, then save as `start.bat`. Run `start.bat`.
##### Unix (linux/mac)
Before you start you must modify the `start.template.sh` file, modify lines 9-16 with your respective values, then save as `start.sh`. Run `start.sh`.

_Below is things I need to do before the personal version is completely ready, if there is anything you think I need to add raise an issue on github_


---
# TODO

**Check for errors**
 - [ ] Auto functions timing
   + [x] Possibly create a new auto function dispatcher loop


 **Clean up code**
  - [ ] Remove duplicate imports
  - [ ] Remove files not used
  - [ ] Standardise module names and content
  - [ ] Give descriptions to important functions
  - [ ] Rename module containers (modules, imagegeneration, dataretrieval, codemodules -> merge utils & datamanagement)


**Helper code**
  - [ ] Create installer script
    + [ ] Clone repo
    + [ ] Create database (possibly convert to sqlite database instead of postgres or give option of either)
    + [ ] Ask for values (keys, other options)
    + [ ] Create starter script
  - [ ] Create starter script (new)
    + [ ] Must work linux + windows
    + [ ] Possibly accept argv for bot management such as updating env vars
      + [ ] Update (pull) repo (optional?)
      + [ ] Update PIP requirements (Maybe allow PIPEnv)
      + [ ] Check database running (postgres only), start if not
      + [ ] ? Possibly connect to database and check tables are setup correctly
      + [ ] Start bot
