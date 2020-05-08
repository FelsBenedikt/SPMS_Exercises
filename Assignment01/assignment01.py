import sys
import pandas as pd
import numpy as np
from numpy.random import random_sample
from scipy.special import lambertw
import math
import os

assert (sys.version_info[0]==3), "This is a Python3.X code and you probably are using Python2.X"

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
LATITUDE_TO_M_CONSTANT = 111000
LONGITUDE_AT_EQUATOR_IN_M_CONSTANT = 111321
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

print("data loaded")
########################################################
#                                                      #
# Task 1: Calculate distance between two given points  #
#      Please, solve this task here and document       #
#       your code                                      #
########################################################
def get_distance_in_meters(lat1, lon1, lat2, lon2):
    lat_dist_in_m = (lat2-lat1)*LATITUDE_TO_M_CONSTANT
    lon_dist_at_lat = LONGITUDE_AT_EQUATOR_IN_M_CONSTANT * (math.cos(rad_of_deg(lat1)) + math.cos(rad_of_deg(lat2))) / 2 # using average. should be ok since only looking at short distances
    lon_dist_in_m = (lon2-lon1) * lon_dist_at_lat
    distance = round(np.sqrt(lon_dist_in_m**2 + lat_dist_in_m**2)) # using pythagoras
    return distance

#########################################################
#                                                       #
#   Task 2: Match users with POIs                       #
#   #  Please, solve this task here and document        #
#       your code                                       #
##########################################################
def find_poi_with_min_dist(lat, lon):
    min_dist = 1000000
    poi_id = -1
    for i in range(len(poi_data[:,0])):
        dist = get_distance_in_meters(lat,lon,poi_data[i,2],poi_data[i,3])
        if dist < min_dist:
            min_dist = dist
            poi_id = poi_data[i,0]
    return poi_id

user_at_poi = [] # list with POIs by user ID

for i in range(len(taxi_data)):
    poi_id = find_poi_with_min_dist(taxi_data[i, 4], taxi_data[i, 3])
    user_at_poi.append(poi_id)


#########################################################
#                                                       #
#  Task 3: Apply Location Privacy Protection Mechanism  #
#                                                       #
##########################################################
#apply Geo-Indistinguishability
noisy_latitude= []
noisy_longitude= []

for user in range(len(taxi_data)):
    r, theta = compute_noise(epsilon)
    lat_noise, lon_noise = addVectorToPos(lat[user], lon[user], r, theta)
    # write output (with same precision as in original data)
    noisy_lat = round(lat_noise, 5)
    noisy_lon = round(lon_noise, 5)
    noisy_latitude.append(lat_noise)
    noisy_longitude.append(lon_noise)



#########################################################
#                                                       #
#  Task4 & Task 5: Measure Privacy Gain & Utility Loss  #
#  Please, solve these two tasks here and document      #
#  your code                                            #
##########################################################
noisy_user_at_poi = []

for i in range(len(taxi_data)):
    noisy_poi_id = find_poi_with_min_dist(noisy_latitude[i], noisy_longitude[i])
    noisy_user_at_poi.append(noisy_poi_id)
correctly_identified = len(set(user_at_poi).intersection(set(noisy_user_at_poi)))   # number of correctly identified user locations
privacy_gain = 1 - correctly_identified/len(user_at_poi)
print(f'privacy gain: {int(100*privacy_gain)}%')

## Utility loss
# Idea: calculate distance to POI location from obfuscated (noisy) location
# and subtract distance to POI from original location

total_extra_dist = 0
for i in range(len(taxi_data)):
    poi_id = user_at_poi[i]
    obfuscated_distance_to_poi = get_distance_in_meters(noisy_latitude[i], noisy_longitude[i], poi_data[poi_id, 2], poi_data[poi_id, 3])
    actual_distance_to_poi = get_distance_in_meters(taxi_data[i, 4], taxi_data[i, 3], poi_data[poi_id, 2], poi_data[poi_id, 3])
    diff = obfuscated_distance_to_poi - actual_distance_to_poi
    total_extra_dist += diff # there is a possibility that a user's location will be closer to the POI. In that case diff is negative; the user will have to walk less.

utility_loss = total_extra_dist/len(taxi_data)
print(f'utility loss: {int(utility_loss)}m additional walking distance')