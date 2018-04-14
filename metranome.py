#!/usr/bin/env python3

import json
from pprint import pprint
import datetime
import os
import urllib.request
import time

#This function is passed a date and will return a list of service ID's that are operating on the given date.  Will return empty list if nothing matches

def getTrainData():
#trying out using time instead of datetime - why? -- "time module is principally for working with unix time stamps; expressed as a floating point number taken to be seconds since the unix epoch. the datetime module can support many of the same operations, but provides a more object oriented set of types, and also has some limited support for time zones."
	if not os.path.exists('./traindata'):
		os.makedirs('./traindata')
		#get all files
		with urllib.request.urlopen("http://maps.googleapis.com/maps/api/geocode/json?address=google") as url:
			data = json.loads(url.read().decode())
		with open('traindata/data.json', 'w') as outfile:
    			json.dump(data, outfile)
	else: 
		t = time.time()
		mtime=os.path.getmtime('traindata/data.json')
		print(mtime)
		print(t)
		#check for file creation times



def getTodayServiceIdList(date):
        #date the given day of the week as a word and string (i.e. wednesday, thursday)
	dayofweek=date.strftime("%A").lower()
        #get today's date in format YYYYMMDD (i.e. 20180412) so we can do simple math on the feed's given date
	compatDate=date.strftime("%Y%m%d").lower()
        #open the calendar.json file we get from our source
	with open('calendar.json') as cal_file:    
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
	with open('trips.json') as trips_file:
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
	with open('stop_times.json') as stops_file:
		stops = json.load(stops_file)
	#open trip updates file.  I don't fully understand this file, but it seems to have a temporal element to it. I think it may only contain trains that have left the station and not yet arrived.  somthing like that.
	with open('tripUpdates.json') as updates_file:
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
		#print(departTimeString)
		departTime=datetime.datetime.strptime(departTimeString,"%H:%M:%S:%Y%m%d") #format departure_time : "06:23:00"
		if departTime < now+datetime.timedelta(minutes=minutesForward) and departTime > now-datetime.timedelta(minutes=minutesPast):
			if trip['update'] is not None:
				for stop in trip['update']['trip_update']['stop_time_update']:
					if stop['stop_id']==trip['stop_id']:
						trip['delay']=stop['departure']['delay']
			else:
				trip['delay']=0
#			print(departTime,departTime+datetime.timedelta(seconds=trip['delay']))
			mylist.append({'trip_id':trip['trip_id'],'stop_id':trip['stop_id'],'depart_time':departTime+datetime.timedelta(seconds=trip['delay']),'scheduled_depart_time':departTime})	
	return mylist
#		print(departTime,trip['update'])
		#print(trip)
# datetime.now() - timedelta(seconds=60)

today = datetime.datetime.now()
#today = datetime.datetime.strptime("2018-04-13 17:40:00","%Y-%m-%d %H:%M:%S")
servicelist=getTodayServiceIdList(today)
stations=["Millennium Station"]
tripslist=getValidTrips(servicelist,stations)
stoplist=["18TH-UP", "MCCORMICK"]
poop=getStopTimes(tripslist,stoplist)
nextlist=getUpCommingTrains(poop,"360",today)
pprint(nextlist)
getTrainData()
#print(json.dumps(poop))
#print(tripslist)

    #for key, value in trip.items():
    #   print (key, value)
