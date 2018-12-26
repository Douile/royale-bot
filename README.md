# Royale Bot _Personal_
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
Before you run you must modify the `start.bat` file, modify lines 9-16 with your respective values. Then run `start.bat`.
##### Unix (linux/mac)
Before you start you must modify the `start.sh` file, modify lines 9-16 with your respective values. Then run `start.sh`.
