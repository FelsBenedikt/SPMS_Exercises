# copy import to copy the value of a variable
import copy
import sys
import pandas as pd
import numpy as np
from numpy.random import random_sample
from scipy.special import lambertw
import math
import os
# csv import to generate a csv file with the results
import csv

# Additional Import for task one (too lazy to calculate the distance by hand)
import geopy.distance

assert (sys.version_info[0] == 3), "This is a Python3.X code and you probably are using Python2.X"


#########################################
#
# Add the generated noise directly on the
# gps coordinates
# Don't modify this!
#########################################
def addVectorToPos(original_lat, original_lon, distance, angle):
    ang_distance = distance / RADIANT_TO_KM_CONSTANT
    lat1 = rad_of_deg(original_lat)
    lon1 = rad_of_deg(original_lon)

    lat2 = math.asin(math.sin(lat1) * math.cos(ang_distance) +
                     math.cos(lat1) * math.sin(ang_distance) * math.cos(angle))
    lon2 = lon1 + math.atan2(
        math.sin(angle) * math.sin(ang_distance) * math.cos(lat1),
        math.cos(ang_distance) - math.sin(lat1) * math.sin(lat2))
    lon2 = (lon2 + 3 * math.pi) % (2 * math.pi) - math.pi  # normalise to -180..+180
    return deg_of_rad(lat2), deg_of_rad(lon2)


#############################################
#
# Useful for the addVectorToPos function
# Don't modify this!
############################################
def rad_of_deg(ang): return ang * math.pi / 180


def deg_of_rad(ang): return ang * 180 / math.pi


def compute_noise(param):
    epsilon = param
    theta = random_sample() * 2 * math.pi
    r = -1. / epsilon * (np.real(lambertw((random_sample() - 1) / math.e, k=-1)) + 1)
    return r, theta
############################################################

#############################################
#
# Constants used in the implementation
# Don't modify this!
############################################
RADIANT_TO_KM_CONSTANT = 6371.0088
epsilon = 1.6/0.05

#########################################################
#                                                       #
#         Load Data from CSV files                      #
#         Don't Modify this!                            #
##########################################################
###load user location data###
df1 = pd.read_csv(os.path.abspath('cleaned_yellow_tripdata_2013-06.csv'), header=0)
df1 = df1.head(100)
df1["pickup_latitude"] = pd.to_numeric(df1["pickup_latitude"])
df1["pickup_longitude"] = pd.to_numeric(df1["pickup_longitude"])
lat = df1["pickup_latitude"].values
lon = df1["pickup_longitude"].values
df1 = df1.apply(pd.to_numeric, errors='coerce')
taxi_data = np.array(df1)
df1 = df1.apply(pd.to_numeric, errors='coerce')
###load POI location data###
df2 = pd.read_csv('pois_pandas.csv', header=0)
df2["poi_id"] = pd.to_numeric(df2["poi_id"])
df2["lat"] = pd.to_numeric(df2["lat"])
df2["lon"] = pd.to_numeric(df2["lon"])
poi_data = np.array(df2)


########################################################
#                                                      #
# Task 1: Calculate distance between two given points  #
#      Please, solve this task here and document       #
#       your code                                      #
########################################################
def get_distance_in_meters(lat1, lon1, lat2, lon2):
    # creating tuples of the coordinates (geopy library required tuples)
    place1 = (lat1, lon1)
    place2 = (lat2, lon2)

    # the geopy.distance.distance function returns the distance between to positions
    # adding the ".m" at the and returns the distance in meters (as requested)
    distance = geopy.distance.distance(place1, place2).m
    return distance

#########################################################
#                                                       #
#   Task 2: Match users with POIs                       #
#   #  Please, solve this task here and document        #
#       your code                                       #
##########################################################


#########################################################
#                                                       #
#  Task 3: Apply Location Privacy Protection Mechanism  #
#                                                       #
##########################################################
# apply Geo-Indistinguishability

# function to add noise to the actual positions
# the function does contain the given code from the assignment01.py
def addNoise2Position():
    noisy_latitude = []
    noisy_longitude = []

    for user in range(len(taxi_data)):
        r, theta = compute_noise(epsilon)
        lat_noise, lon_noise = addVectorToPos(lat[user], lon[user], r, theta)
        # write output (with same precision as in original data)
        noisy_lat = round(lat_noise, 5)
        noisy_lon = round(lon_noise, 5)
        # the arrays contain the noisy values of the longitude and latitudes
        noisy_latitude.append(noisy_lat)
        noisy_longitude.append(noisy_lon)
    return noisy_latitude, noisy_longitude


task2UserPoiArray = []


# function to map the pickup location of a user to a POI location
# optional paramter "noisy" for task 4 and 5
def mapUser2Poi(input_taxi_data, input_poi_data, noisy=False):
    # clean up array
    global task2UserPoiArray
    del task2UserPoiArray[:]
    # (Task 4, 5) create the arrays with noisy values of the longitude/latitude
    if noisy:
        noisyLatArray, noisyLonArray = addNoise2Position()
    # iterate through the pickup locations / the users to map the nearest POI location to the pickup location
    for pickupLocation in taxi_data:
        # the userID is contained in the first column of the taxi data
        userID = int(pickupLocation[0])
        # only use the noisy longitude/latitude if requested (Task 4, 5)
        if noisy:
            lon1 = noisyLonArray[userID]
            lat1 = noisyLatArray[userID]
        else:
            # in Task 2 there is no need to use the noisy values.
            # the longitude and the latitude are presented in the taxi data set
            lon1 = pickupLocation[3]
            lat1 = pickupLocation[4]
        # reset minimum Distance (used to map the location to a poi)
        minimumDistance = None
        userPoiMatch = ''
        # cicle through the poi data set to find the nearest POI location for the spectated pickup location of the user
        for poi in poi_data:
            # latitude and longitude of the poi locations come from the poi data set
            lat2 = poi[2]
            lon2 = poi[3]
            # use the function from task 1 to calculate the distance between two locations
            calculatedDistance = get_distance_in_meters(lat1, lon1, lat2, lon2)
            # set the minimum distance to the calculated one if it is not set yet or
            # if the newly calculated distance is smaller than the currently saved one
            if not minimumDistance or minimumDistance > calculatedDistance:
                # items: poiID, poiCategory, pickupLongitude, pickupLatitude
                userPoiMatch = [poi[0], poi[1], lon1, lat1]
                minimumDistance = calculatedDistance
        # write the result into a array
        task2UserPoiArray.append(userPoiMatch)
    return task2UserPoiArray

# Small printing segment to inform the user of the script what is happening right now
print('Starting Task 2.')
tmpArray = mapUser2Poi(input_taxi_data=taxi_data, input_poi_data=poi_data)
# here the copy.deepcopy is needed to prevent overwriting the variable
# (maybe there is a easier way to prevent this but thi   s does the job)
originalDataUserPoiArray = copy.deepcopy(tmpArray)
print('Task 2 completed.')

#########################################################
#                                                       #
#  Task4 & Task 5: Measure Privacy Gain & Utility Loss  #
#  Please, solve these two tasks here and document      #
#  your code                                            #
##########################################################

##### Task4 - Privacy Gain #####
print('Starting Task 4.')
# this time the mapUser2Poi function is called with the noisy=True parameter to add noise to the locations
tmpArray = mapUser2Poi(input_taxi_data=taxi_data, input_poi_data=poi_data, noisy=True)
# again used the copy.deepcopy helper
noisyDataUserPoiArray = copy.deepcopy(tmpArray)
# only continue if the two arrays have the same length
# if they are not the same length the implementation can't be correct.
if len(originalDataUserPoiArray) != len(noisyDataUserPoiArray):
    print('the code seems to contain a bug.')
else:
    # create a array which will contain the results of the tasks
    csvPrintArray = []
    # counter variable that gets increased if the mapped poi location (noisy)
    # is another one then with the original locations. Used to calculate the privacy gain.
    differentPoiResultCounter = 0
    # iterate through the (currently 100) rows of the noisyDataUserPoiArray and compare the results
    for item in range(len(noisyDataUserPoiArray)):
        # if the mapped POI location (noisy) is the same as with original location set the samePOIResult varible to "True"
        # else the variable is set to "False" and the counter gets increased by one.
        # The samePOIResult variable is used for the result output in the csv file.
        if originalDataUserPoiArray[item][0] == noisyDataUserPoiArray[item][0]:
            samePoiResult = "True"
        else:
            samePoiResult = "False"
            differentPoiResultCounter +=1
        # generate big array to print the results to a csv:
        # format: userID, poiID(original), poiCategory(original), pickup_longitude(original), pickup_latitude(original),
        #         poiID(noisy), poiCategory(noisy), pickup_longitude(noisy), pickup_latitude(noisy), samePOI
        row4csv = [int(taxi_data[item][0])]
        row4csv.extend(originalDataUserPoiArray[item])
        row4csv.extend(noisyDataUserPoiArray[item])
        row4csv.append(samePoiResult)
        csvPrintArray.append(row4csv)
    # calculate the percentage of Privacy gain:
    privacyGain = ((differentPoiResultCounter/len(csvPrintArray))*100)
    print(str(differentPoiResultCounter) + ' of ' + str(len(csvPrintArray)) + ' assigned POIs were wrong.')
    print('This results in a privacy gain of ' + str(privacyGain) + '%')
    print('Task 4 completed.')

##### Task 5 - Utility loss #####
print('Starting Task 5.')
# again a small test if the arrays do contain the same amount of entries
if len(originalDataUserPoiArray) != len(noisyDataUserPoiArray):
    print('the code seems to contain a bug.')
else:
    # variable that contains the sum of the additional distance the user has to walk to get to the "noisy" location
    sumOfDistance = 0
    # iterate through the array with the results to collect the required longitude and latitude values
    # these values (actual and noisy locations) are used to calculate the additional distance for the user
    for item in csvPrintArray:
        lat1 = item[4]
        lon1 = item[3]
        lat2 = item[8]
        lon2 = item[7]
        # add the calculated additional distance to the sum variable
        tmpDiff = get_distance_in_meters(lat1, lon1, lat2, lon2)
        sumOfDistance += tmpDiff
        # the (additional walking) distance is also added to the csvPrintArray
        item.append(round(tmpDiff, 2))
    # calculate the average additional distance in meters
    averageAdditionalDistance = round(sumOfDistance/len(csvPrintArray), 2)
    print('In average each user has to walk additional ' + str(averageAdditionalDistance) + 'm to the new location.')
    print('Task 5 completed.')

# additional (not required) write all the values to a csv file to be able to inspect the results.
# the csv file is written the the assignment1Results.csv within the same directory as the script itself
f = open('assignment1Results.csv', 'w')
with f:
    writer = csv.writer(f)
    # These are the headlines of the columns (added for increased usability)
    headerRow = ["userID", "poiID(original)", "poiCategory(original)", "pickup_longitude(original)",
                 "pickup_latitude(original)", "poiID(noisy)", "poiCategory(noisy)",
                 "pickup_longitude(noisy)", "pickup_latitude(noisy)", "samePOI", "distanceOriginalNoisy"]
    writer.writerow(headerRow)
    for entry in csvPrintArray:
        writer.writerow(entry)
