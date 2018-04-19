#!/usr/bin/env python3

import json
from pprint import pprint
import datetime
import os
import urllib.request
import time
import config

#-------------------------------Get New Data from Metra api-----------------------------------#
# hobbled little bit that checks if there are new files up or files that are too old locally and gets new ones
# most files should only be updates if there is a new schedule publish time or if the files are > 1 day old.  Sort of redundant I supposed, but whatever
def getTrainData():
	#use config to store api keys and secrets. Need to make config.py file in the same dir as the code with api_key and api_secret params
	apiKey=config.api_key
	apiSecret=config.api_secret
	apiUrlBase='https://gtfsapi.metrarail.com/gtfs'#Metra api base url path
	daily=86400 
	dailyList=["/schedule/calendar","/schedule/trips","/schedule/stops","/schedule/stop_times","/raw/published.txt","/raw/schedule.zip"]
	minutely=45
	minutelyList=["/tripUpdates"]
	getDailys=0
	#time seems to be easier when you're pulling a unix file time 
	curtime = time.time()
	
	#thank you here for help with this how to do this - https://stackoverflow.com/questions/44239822/urllib-request-urlopenurl-with-authentication
	#great auth realm for series of requests that my follow form here
	password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, apiUrlBase, apiKey, apiSecret)
	handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
	opener = urllib.request.build_opener(handler)
	
	if not os.path.exists('./traindata'):#gave up on not hardcoding thigs, maybe later
		os.makedirs('./traindata')
		print("made traindata dir")
	if not os.path.exists('./traindata/published.txt'):
		getDailys=1
	elif  os.path.exists('./traindata/published.txt'):
		with open('./traindata/published.txt', 'r') as pubfile:
			data=pubfile.read() 
		pubFileTime=datetime.datetime.strptime(data,"%m/%d/%Y %H:%M:%S %p")
		with opener.open(apiUrlBase+"/raw/published.txt") as url:
			data=url.read().decode()
		pubUrlTime=datetime.datetime.strptime(data,"%m/%d/%Y %H:%M:%S %p")
		mtime=os.path.getmtime('./traindata/published.txt')
		if pubUrlTime>pubFileTime or mtime<curtime-daily:	
			getDailys=1
			with open("./traindata/published.txt", "w") as outfile:
				outfile.write(data)
			dailyList.remove("/raw/published.txt")
			print('Need to get new dailys')
	if getDailys==1:
		for download in dailyList:
			if download.replace("/raw/","")=="published.txt":
				with opener.open(apiUrlBase+download) as url:
					data=url.read().decode()
				with open("./traindata/"+download.replace("/raw/",""),'w') as outfile:
					outfile.write(data)
			elif download.replace("/raw/","")=="schedule.zip":
				with opener.open(apiUrlBase+download) as url:
					data=url.read()
				with open("./traindata/"+download.replace("/raw/",""),'wb') as outfile:
					outfile.write(data)
			else:
				with opener.open(apiUrlBase+download) as url:
					data = json.loads(url.read().decode())
				with open("./traindata/"+download.replace("/schedule/","")+".json", 'w') as outfile:
					json.dump(data, outfile)
		print('Got Daily File Refresh')
	else:
		print("Daily files are up to date")

	for download in minutelyList:
		if not os.path.exists('./traindata'+download+'.json'):
			with opener.open(apiUrlBase+download) as url:
				data = json.loads(url.read().decode())
			with open('./traindata'+download+'.json', 'w') as outfile:
    				json.dump(data, outfile)
			print("no tripUpdate file there, so its been downloaded")
		else: 
			mtime=os.path.getmtime('./traindata'+download+'.json')
			if mtime < curtime-minutely:
				with opener.open(apiUrlBase+download) as url:
					data = json.loads(url.read().decode())
				with open('./traindata'+download+'.json', 'w') as outfile:
					json.dump(data, outfile)
				print("New tripUpdate file needed, so its been downloaded"+" It was "+str(curtime-mtime)+" seconds old")
			else:
				print("tripUpdate file is up to date, no download")
			print(mtime,curtime)

#This function is passed a date and will return a list of service ID's that are operating on the given date.  Will return empty list if nothing matches
def getTodayServiceIdList(date):
        #date the given day of the week as a word and string (i.e. wednesday, thursday)
	dayofweek=date.strftime("%A").lower()
        #get today's date in format YYYYMMDD (i.e. 20180412) so we can do simple math on the feed's given date
	compatDate=date.strftime("%Y%m%d").lower()
        #open the calendar.json file we get from our source
	with open('./traindata/calendar.json') as cal_file:    
		calendar = json.load(cal_file)

	mylist=[]
        #loop through each entry and determine if today has a bit set to 1 and if the date is between the start date and end date.  Format of an entry is below. 
	#{'service_id': 'C1', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1, 'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': '2018-04-21', 'end_date': '2018-04-27'}
	for record in calendar:
		dayTest=record[dayofweek]
                #remove the - from the dates 
		startDate=record['start_date'].replace("-","").strip()
		endDate=record['end_date'].replace("-","").strip()
		if dayTest==1 and compatDate<=endDate and compatDate>=startDate:
			mylist.append(record['service_id'])
	return mylist

def getValidTrips(serviceIdList,dstStationList):
	#{  "route_id": "UP-W",  "service_id": "C3",  "trip_id": "UP-W_UW517_V7_C",  "trip_headsign": "Elburn",  "block_id": "",  "shape_id": "UP-W_OB_1",  "direction_id": 0  }
	with open('./traindata/trips.json') as trips_file:
		trips = json.load(trips_file)
	mylist=[]
	for trip in trips:
		tripServiceId=trip['service_id']
		tripDirection=trip['trip_headsign']
		if tripServiceId in serviceIdList and tripDirection in dstStationList: 
                        mylist.append(trip['trip_id'])
	return mylist
	
    
def getStopTimes(tripIdList,stopsList):
#{"trip_id":"BNSF_BN1200_V1_A","arrival_time":"04:30:00","departure_time":"04:30:00","stop_id":"AURORA","stop_sequence":1,"pickup_type":0,"drop_off_type":0,"center_boarding":0,"south_boarding":0,"bikes_allowed":1,"notice":0}
	with open('./traindata/stop_times.json') as stops_file:
		stops = json.load(stops_file)
	#open trip updates file.  I don't fully understand this file, but it seems to have a temporal element to it. I think it may only contain trains that have left the station and not yet arrived.  somthing like that.
	with open('./traindata/tripUpdates.json') as updates_file:
		updates = json.load(updates_file)
	mylist=[]
	for stop in stops:	
		stopId=stop['stop_id']
		tripId=stop['trip_id']
		#give this stop an update key that is set to none by default
		stop['update']=None
		#logic to identify a stop that is in the list of both stops and trips provided to the function 
		if stopId in stopsList and tripId in tripIdList:
			#this loops through the updates file and attempts match a trip that has an update. 
			#if an update is found, append it to the stop dictionary 
			for update in updates:
				if tripId==update['id']:	
					stop['update'] = update
			#add stop dictionary to mylist
			mylist.append(stop)
	#return a list of dictionaries containing matches of valid stops, and trips given the input to the function with added update information
	return mylist

def getUpCommingTrains(trips,minutesout,date):
	minutesPast=10
	minutesForward=int(minutesout)
	#get the current time
	#this is inconsistant being in the function here -fix
	#now=datetime.datetime.strptime("2018-04-13 17:40:00","%Y-%m-%d %H:%M:%S")
	now=date
	#now=datetime.datetime.now()
	mylist=[]
	for trip in trips:
		#this little convoluted fun has to be done because trips that red-eye to a new day go into hours above 24.  python's datetime doesn't really like that. Here some convoluted thing to get it the way I expect it 
		testTime=trip['departure_time'].split(':')[0]
		timeTail=now.strftime("%Y%m%d")
		if int(testTime) > 23:
			newHour=int(testTime)-24
			if newHour<10:
				newHourFinal="0"+str(newHour)
			else:
				newHourFinal=str(newHour)
			silly=now+datetime.timedelta(days=1)
			timeTail=silly.strftime("%Y%m%d")
		else:
			newHourFinal=testTime
		departTimeString=newHourFinal+":"+trip['departure_time'].split(':')[1]+":"+trip['departure_time'].split(':')[2]+":"+timeTail
		departTime=datetime.datetime.strptime(departTimeString,"%H:%M:%S:%Y%m%d") #format departure_time : "06:23:00"
		if departTime < now+datetime.timedelta(minutes=minutesForward) and departTime > now-datetime.timedelta(minutes=minutesPast):
			if trip['update'] is not None:
				for stop in trip['update']['trip_update']['stop_time_update']:
					if stop['stop_id']==trip['stop_id']:
						trip['delay']=stop['departure']['delay']
					else:
						#not sure if this will cause misreporting, but it seems to be needed because a trip update file may not have full update information for each stop
						#So, if the stop we're looking for is not in the trip update, just assume there was a 0 delay. 
						#This will probably be confusing since after a train has passed as top, it will get removed from tripUpdates.json.  Since we can still report 
						#trains that have just passed, a delay will dissapear and go to zero, but the next top will still show the delay. 
						#The train doesn't have an overall delay value so the next best thing would be to change this to be filled with the delay of the nearest stop
						#on the list or perhaps the final stop arrival time.  Not going to do that now, so it's gonna be zero... Its a little silly, but 
						#the static destination station I have (i.e. Millennium Station) does not match with the tripUpdate name for it which is MILLENNIUM"
						trip['delay']=0
			else:
				trip['delay']=0
			mylist.append({'trip_id':trip['trip_id'],'stop_id':trip['stop_id'],'depart_time':departTime+datetime.timedelta(seconds=trip['delay']),'scheduled_depart_time':departTime})	
	return mylist

#Manually settings destination station and pickup stations care about
destStations=["Millennium Station"]
pickupStops=["18TH-UP", "MCCORMICK"]

#How many minutes our should we show trains for?
minutesLater="180"

#get current time for passing to functions 
today = datetime.datetime.now()
#manually override time for testing with below, adjust time as needed 
#today = datetime.datetime.strptime("2018-04-13 17:40:00","%Y-%m-%d %H:%M:%S")

#check if there is new train data
getTrainData()

#figure out stuff 
servicelist=getTodayServiceIdList(today)
tripslist=getValidTrips(servicelist,destStations)
stopTimes=getStopTimes(tripslist,pickupStops)
nextTrains=getUpCommingTrains(stopTimes,minutesLater,today)

#print results

nownow = datetime.datetime.now()
for train in nextTrains:
	timeTilTrain=train['depart_time']-nownow
	print(train['stop_id']," in ",int(timeTilTrain.total_seconds()/60)," minutes")
#pprint(nextTrains)
#print(json.dumps(nextTrains))
