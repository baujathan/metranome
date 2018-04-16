# Metranome
Because this was the first word I could think of that had Metra in it. Perhaps I'll change it with something that makes sense.  

## What it do
This polls [Metra's api](https://metrarail.com/developers/metra-gtfs-api) to schedule info and real-time updates and then will print out upcoming trips for given stops and destinations.   

## Why it be
Made this for a home infoboard so I could have display that came on in the morning and would show me upcomming trains, their delays, which stop I should go to.  I'm very groggy in the morning and I have two train stations near me I can catch a train to.  They are ofcourse a different distance and I sometimes mix up how long it takes me to get to one vs. the other.  They have different train schedules. Finally trains have delays and when you're always running late, as I am, it'd be nice to know about them.  I ofcourse could use a phone app to sorth this out, but I'm groggy and I don't.  So, I wanted to build a board that solved this problem, displaying this in my bedroom, kitchand, and on my TV.  This is the fist step... get data.  Using it is a different project.   

## Requirements
* Live in chicago, I can't imagine any use for someone who doesn't 
* Request an apikey from metrarail.com's website 
* put said apikeys in a config.py file in the same directory as this script:
```
api_key = '<key here>'
api_secret = '<secret here>'
```
* update with relevant information for your use and do something useful for yourself with the outputs.  In current state, its probably not immediately useful for anyone. 


