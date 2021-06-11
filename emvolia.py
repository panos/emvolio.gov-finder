import requests
import json
import csv

from datetime import datetime
from config import *

emvoliastika = set()

'''
Instructions for obtaining your personId and your Authorization header:
- Use Google Chrome or any other browser that allows you to debug HTTP requests.
- Login to https://emvolio.gov.gr normally.
- You can find your personId and your Authorization header by hitting the F12 key
  and selecting the Network -> Requests and Header tab.
'''

# "selectedDate": '2021-'+ month + '-' + day + 'T00:00:00+03:00',
if month < 10:
    date_part_1 = '2021-0' + str(month) + '-'
else:
    date_part_1 = '2021-' + str(month) + '-'

date_part_3 = '-T00:00:00+03:00'

my_headers = {'Authorization': authorization}

'''
This repository supplies two different .csv datasets:
- tkAttiki.csv: includes zip codes for Attica region 
- tkGreece.csv: includes all the Greek zip codes
'''
if datasetComplete == False:
    with open('tkAttiki.csv', 'r', encoding="utf8") as TK: # See: tkGreece.csv

        reader = csv.reader(TK)

        for row in reader:
            print("-----------------------------------")
            print("ZIP CODE: {}, AREA: {}".format(row[0], row[2]))
            print("-----------------------------------")

            response = requests.post("https://emvolio.gov.gr/app/api/CovidService/CV_User_NearCenters",
                                     {"zipCode": row[0], "personId": personId}, headers=my_headers)

            if 'exceptionObject' not in response.json().keys():
                # print(response.json())
                centers = response.json().get('centers')

                if len(centers) > 0:
                    print("VACCINATION CENTERS - {}".format(row[2]))
                    print("-----------------------------------")

                    print(response.json())
                    for center in centers:
                        emvoliastika.add((center.get('name'), center.get('id'),center.get('tk'), response.json().get('startDate')))

                    print(emvoliastika)

    # we write the list of vaccination centers (name, id, zip code, start date in emvoliastika.json file
    with open('emvoliastika.json', 'w', encoding="utf8") as fp:
        json.dump(list(emvoliastika), fp)
    fp.close()

with open('emvoliastika.json', 'r', encoding="utf8") as fp:
    reader = json.load(fp)

    for key in reader:
        print("-----------------------------------")
        print("CHECKING {}".format(key[0]))
        print("(ID: {}, ZIP: {})".format(key[1], key[2]))
        print("-----------------------------------")

        # because the start date might not be available, we search for a range of days after the start date (be careful if month changes also)
        for i in range(day, 6):
            day_str = str(day + i)

            response = requests.post("https://emvolio.gov.gr/app/api/CovidService/CV_TimeSlots_Free",
                                     {"centerId": key[1], "personId": personId, "firstDoseDate": "null",
                                      "zoneNum": "null",
                                      "selectedDate": date_part_1 + day_str + date_part_3,
                                      "dose": "1",
                                      "requestRecommended": "true"},
                                      headers=my_headers)

            if 'exceptionObject' not in response.json().keys():
                print("-----------------------------------")
                print("APPOINTMENTS FOUND!")
                print("VACCINATION CENTER (Single dose): " + str(key[0]))
                print("-----------------------------------")

                # print(response.json())

                for i, percent in enumerate(response.json()['timeslotsFree']):

                    if response.json()['timeslotsFree'][i]['percentAvailable'] > 0:
                        if doubleDose == False:
                            print("-----------------------------------")
                            print("VACCINATION CENTER (Single dose): " + str(key[0]))
                            print("-----------------------------------")
                            print("Zip code: " + str(key[2]))
                            print("Vaccination center: ", key[0])
                            print("Vaccination center number: ", key[1])
                            print("Available date of 1st vaccination " + response.json()['timeslotsFree'][i]['onDate'])
                            print("-----------------------------------")
                        else:
                            response2 = requests.post("https://emvolio.gov.gr/app/api/CovidService/CV_TimeSlots_Free",
                                                      data={"centerId": key[1], "personId": personId,
                                                            "firstDoseDate": response.json()['timeslotsFree'][i]['onDate'],
                                                            "zoneNum": "null", "selectedDate": response.json()['timeslotsFree'][i]['onDate'],
                                                            "dose": "2", "requestRecommended": "true"}, headers=my_headers)

                            # Attempts to fetch a date for the second vaccination appointment, if a start
                            # date exists for a specific vaccination center.
                            for j, percents in enumerate(response2.json()['timeslotsFree']):

                                if response2.json()['timeslotsFree'][j]['percentAvailable'] > 0:
                                    date_time_0 = datetime.strptime(response.json()['timeslotsFree'][i]['onDate'],
                                                                    '%Y-%m-%dT%H:%M:%S+03:00')

                                    date_time_1 = datetime.strptime(response2.json()['timeslotsFree'][j]['onDate'],
                                                                '%Y-%m-%dT%H:%M:%S+03:00')

                                    delta = date_time_1 - date_time_0
                                    # we print the vaccination centers that the available days between the two possible apointments is less than 50 (ie POSSIBLE non Astra Zeneca)
                                    if (delta.days < 50):
                                        print("-----------------------------------")
                                        print("VACCINATION CENTER: " + str(key[0]))
                                        print("-----------------------------------")
                                        print("Zip Code: " + str(key[2]))
                                        print("Vaccination center: ", key[0])
                                        print("Vaccination center number: ", key[1])
                                        print("Available date of 1st vaccination " + response.json()['timeslotsFree'][i]['onDate'])
                                        print("Days between vaccination appointments " + str(delta.days))
                                        print("-----------------------------------")
            else:
                print("Invalid request")
