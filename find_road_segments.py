# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 13:16:40 2018

@author: caoa
"""
import geopandas as gp
import pandas as pd
from shapely.geometry import Point
from scipy.signal import medfilt
from more_itertools import unique_everseen

pd.options.display.max_rows = 16

roads = gp.read_file('washtenaw_roads.shp')
sidx = roads.sindex
print("Finished reading shapefile")

#%%
tripstart = 41100
filenum = 1
filename = 'TripStart_{0}_p{1:0>3}.csv'.format(tripstart,filenum)
columns = ['RxDevice','FileId','TxDevice','Gentime','TxRandom',
           'MsgCount','DSecond','Latitude','Longitude','Elevation',
           'Speed','Heading','Ax','Ay','Az',
           'Yawrate','PathCount','RadiusOfCurve','Confidence']

trip = pd.read_csv(filename, header=None, names=columns)

#%% Reduce precision to 4 decimals and remove duplicate gps coordinates
trip[['Latitude','Longitude']] = trip[['Latitude','Longitude']].round(4)
trip.drop_duplicates(['Latitude','Longitude'], keep='first', inplace=True)
# sample remaining points
N = 10
trip_sample = trip.iloc[::N].reset_index()

#%% Find nearest road
radius = 0.0001
closest_road = []
gps = zip(trip_sample['Longitude'],trip_sample['Latitude'])
for i, xy in enumerate(gps):
    pt = Point(xy)
    road_id = list(sidx.nearest(pt.buffer(radius).bounds, 1))
    road_dist = [(id,roads.at[id,'geometry'].distance(pt)) for id in road_id]
    road_dist.sort(key=lambda x: x[1])
    closest_road.append(road_dist[0])

#%% Merge with trip data
nearest_rd = pd.DataFrame(closest_road, columns=['rd1','d1'])
trip_segments = pd.concat([trip_sample, nearest_rd], axis=1)
# apply median filter to roads to try to remove spurious intersections
trip_segments['rd1'] = medfilt(trip_segments['rd1'],9).astype(int)

#%% Extract road geometry
for (rx,id,tx), df in trip_segments.groupby(['RxDevice','FileId','TxDevice']):
    print('For trip {},{},{}'.format(rx,id,tx))
    road_segments = list(unique_everseen(df['rd1'].tolist()))
    print(road_segments)
    gdf = roads.loc[road_segments] # plot the geometry in this geoDataFrame
    break # first trip only

    
