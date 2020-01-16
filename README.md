# new-artists-twitter-bot

A Twitter bot that tweets whenever a artist is playing their first concert in DC. 

[Check it out here](https://twitter.com/firstshowindc). 

Made by Jake Gluck [jagluck.github.io](jagluck.github.io).   
jakeagluck@gmail.com

Please reach out with questions.

# Code

### Here is how it works at a high level

We use two sources of data.
1. The songkick api
2. The Twitter api

The code runs on a Heroku server and uses a postgres database to store items to tweet and recently sent tweets. 

There are two functions that kick off the bot.

```onceADay():``` This runs every morning. It gets data from songkick for concerts in the next three days. For each artist it searches through their songkick history and if they have never played in DC before it add them to a list of concerts to tweet. We get the concert times and adjust them slightly for openers (by one second per order in front of headliner) to place openers before headlines. If these are not already in the database we add them.

```everyHour():``` This runs every day between 7am and 9pm. We read from the database and find the most recent concert that hasn't already happened and has not already been tweeted. We send the tweet and update the database that is has been sent. Finally we remove items in the database that are older than two weeks old. 

### Files

[bot.py](bot.py): The main file where all other processes are called from. Contains code that runs once a day and every hour. Also contains code to communicate with Twitter api

[clock.py](clock.py): The file that contains the timers that call code to run.

[config.py](config.py): imports and environmental variables.

[songkick.py](songkick.py): calls to get data from the songkick api

[database.py](database.py): calls to manage and communicate with our database

[requirements.txt](requirements.txt): libraries needed for our environment

[Procfile](Procfile): tells Heroku what to file to run

 
