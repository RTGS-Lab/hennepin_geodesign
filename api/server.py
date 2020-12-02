import string
import topojson as tp
import shapefile
from json import dumps
import zipfile
from io import StringIO
import json
import psycopg2
from shapely import wkt
import geopandas as gpd
import geojson
from geojson import Polygon
import pandas as pd
import os
import urllib3
import requests

from flask import Flask, request
from flask_cors import CORS
app = Flask(__name__) # setup initial flask app; gets called throughout in routes
CORS(app)
#requests.packages.urllib3.disable_warnings()
#requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
#requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
'''
Python decorateors point to a function
Here, it specifies the app route '/'.
It sends basic text from the hello() function
back as a response. This is what you
see in your web browser when you type in
x.x.x.x:5000/

Note: the / in the above path references the '/'
in the @app.route('/') designation.

For more on decorators, Google "decorators in python".
'''
@app.route('/') #python decorator 
def hello_world(): #function that app.route decorator references
  response = hello()
  return response

def hello():
  return "demonstration"

#@app.route('/parcels')
#def getParcels():

 #  with open('/home/shared/data/hennepin_county_parcels_topo.json') as file:
  #     print('starting to read file')
   #    hp_county_topo = json.load(file)
   #print('Read topo json file') 
   #return str(hp_county_topo)
def getFieldCheck(attr, args, query_filter, dataType):
    if attr in args:
        attr_val = args[attr]
        if dataType == 'int':
            op = '>'
        else:
            op = '='
        if dataType == 'str':
            attr_val = "'"+ str(attr_val)+ "'"
        else:
            attr_val = str(attr_val)
        if query_filter == '':
            query_filter = 'WHERE '+ attr + op + attr_val
        else:
            query_filter = (query_filter+ ' AND '+ attr+ op + attr_val)

    return query_filter

def buildQueryFilter(args):
    query_filter = ''
   
    query_filter = getFieldCheck('watqual_c', args, query_filter, 'int')
    query_filter = getFieldCheck('watqual_nc', args, query_filter, 'int')
    query_filter = getFieldCheck('habqual_c', args, query_filter, 'int')
    query_filter = getFieldCheck('habqual_nc', args, query_filter, 'int')
    query_filter = getFieldCheck('pr_typ_nm1', args, query_filter, 'str')
    query_filter = getFieldCheck('parcel_id', args, query_filter, 'str')
    query_filter = getFieldCheck('parcel_area', args, query_filter, 'int')
    query_filter = getFieldCheck('sale_price', args, query_filter, 'int')
    query_filter = getFieldCheck('watershed_', args, query_filter, 'str')
    query_filter = getFieldCheck('mkt_val_to', args, query_filter, 'int')
    query_filter = getFieldCheck('taxable_va', args, query_filter, 'int')
    query_filter = getFieldCheck('land_mv1', args, query_filter, 'int')
    query_filter = getFieldCheck('bldg_mv1', args, query_filter, 'int')
    query_filter = getFieldCheck('total_mv1', args, query_filter, 'int')

    if 'n' in args:
        if query_filter == '':
            query_filter = 'LIMIT ' + str(args['n'])
        else:
            query_filter = query_filter + ' LIMIT ' + str(args['n'])
    return query_filter

LOGICAL_OPERATORS = ("AND", "OR", "and", "or")

COMPARISON_OPERATORS = {
    "lt": "<",
    "gt": ">",
    "lte": "<=",
    "gte": ">=",
    "eq": "=",
    "neq": "!="
}

def process(data):
    """
    :param data: JSON Object (dict). 
    :return: where clause (str) built from data
    """
    where_clause = ""
    if isinstance(data, list):# when multiple queries
        for part in data:
            print("part: "+ str(part))
            if part not in LOGICAL_OPERATORS:
                if part['name'] == 'limit':
                    where_clause += " {} {} ".format(part["name"], part["val"])
                else:
                    where_clause += " ({}) ".format(process(part))

            else:
                where_clause += process(part)
    elif isinstance(data, dict):
        #if 'name' in data and data['name'] == 'limit' :
        #    where_clause += " {} {} ".format(data["name"], data["val"])
        if isinstance(data["val"], str):
            where_clause += " {} {} '{}' ".format(data["name"], COMPARISON_OPERATORS[data["op"]], data["val"])
        else:
          where_clause += " {} {} {} ".format(data["name"], COMPARISON_OPERATORS[data["op"]], data["val"])
    elif isinstance(data, str):
        return data 
   
    if where_clause == "where ":
        return ""
    else:
        return where_clause

@app.route('/parcels')
def getQueryParcels():
    conn = psycopg2.connect(host="35.222.135.127", port = 5432, database="hennepin_geodesign", user="postgres", password="GemsIOT1701")
    cur = conn.cursor()
    args = request.args
    print('query args:'+ str(args))
    if 'q' in args:
        reqParams = json.loads(args['q'])['filters']
        print('req params:'+ str(reqParams))
        where_clause = process(reqParams)
        print('where_clause: ' + where_clause)
    
        result = cur.execute("select parcel_id, parcel_area, sale_price, geom, ST_AsText(geom) AS poly_points,  watqual_c, watqual_nc, habqual_nc, habqual_c, pr_typ_nm1, watershed_, mkt_val_to, taxable_va, land_mv1, bldg_mv1, total_mv1 from parcels.parcels "+ " where "+ where_clause )
    else:
        query_filter = buildQueryFilter(args)
        print('query filter constructed from args:' + query_filter)
        result = cur.execute("select parcel_id, parcel_area, sale_price, geom, ST_AsText(geom) AS poly_points,  watqual_c, watqual_nc, habqual_nc, habqual_c, pr_typ_nm1, watershed_, mkt_val_to, taxable_va, land_mv1, bldg_mv1, total_mv1 from parcels.parcels "+ query_filter )

    query_results = cur.fetchall()
    query_results_df = pd.DataFrame(data = query_results, columns = ['parcel_id', 'parcel_area', 'sale_price', 'geom', 'poly_pts','watQual_c', 'watQual_nc', 'habQual_nc', 'habQual_c', 'pr_typ_nm1','watershed_', 'mkt_val_to', 'taxable_va', 'land_mv1', 'bldg_mv1', 'total_mv1'])
    print("retreived "+ str(query_results_df.shape[0])+ " records")
    query_results_df['poly_pts'] = query_results_df['poly_pts'].apply(wkt.loads)
    query_results_geo_df = gpd.GeoDataFrame(query_results_df, geometry='poly_pts')
    op_geo_json = data2geojson(query_results_geo_df)
    return op_geo_json

@app.route('/nParcelsDB/<int:n>')
def getNDBParcels(n):
    conn = psycopg2.connect(host="35.222.135.127", port = 5432, database="hennepin_geodesign", user="postgres", password="GemsIOT1701")
    cur = conn.cursor()
    result = cur.execute("select parcel_id, parcel_area, sale_price, geom, ST_AsText(geom) AS poly_points,  watqual_c, watqual_nc, habqual_nc, habqual_c from parcels.parcels LIMIT "+ str(n))
    query_results = cur.fetchall()
    query_results_df = pd.DataFrame(data = query_results, columns = ['parcel_id', 'parcel_area', 'sale_price', 'geom', 'poly_pts','watQual_c', 'watQual_nc', 'habQual_nc', 'habQual_c'])
    query_results_df['poly_pts'] = query_results_df['poly_pts'].apply(wkt.loads)
    query_results_geo_df = gpd.GeoDataFrame(query_results_df, geometry='poly_pts')
    op_geo_json_db = data2geojson(query_results_geo_df)
    return op_geo_json_db

def data2geojson(df):
    features = []
    filter_features = lambda X: features.append( geojson.Feature(geometry= X["poly_pts"],\
                        properties=dict(parcel_id = X["parcel_id"], parcel_area = X["parcel_area"],\
                                        sale_price = X["sale_price"], watQual_c = X['watQual_c'], watQual_nc = X["watQual_nc"],\
                                        habQual_nc = X["habQual_nc"], habQual_c = X["habQual_c"], pr_typ_nm1 = X['pr_typ_nm1'],\
                                        watershed_= X['watershed_'], mkt_val_to = X['mkt_val_to'],taxable_va=X['taxable_va'],\
                                        land_mv1 = X['land_mv1'], bldg_mv1 = X['bldg_mv1'], total_mv1 = X['total_mv1']\
                                        )))
    df.apply(filter_features, axis=1)
    op_json = geojson.FeatureCollection(features)  
    #op_topo_json = tp.Topology(features, topology = True)
    #return json.dumps(op_topo_json) 
    #return json.dumps(op_json)
    return op_json

#method to retrieve parcels from json file. takes time since file needs to be loaded for each request  
#@app.route('/nParcels/<int:n>')
#def getTopNParcels(n):
#    with open('/home/shared/data/hennepin_co_parcels_web_geo.json') as file:
#        print('starting to read json file')
#        hp_county_json = json.load(file)
#    # make this based on selection
#    selectedFeatures = []
#    n_features =0
#    for feat in hp_county_json['features']:
#        if n_features< n :
#            selectedFeatures.append(feat)
#            n_features = n_features+1
#    outputGeoJson = {'type': 'FeatureCollection', 'features': selectedFeatures}
#    print('constructed json with selected parcels')
#    jsonStr = json.dumps(outputGeoJson)
#    return jsonStr
#    #TODO Convert Geo to Topo while returning

#TODO Complete thismethod
@app.route('/nParcels')
def convertGeoToTopo(geoJson):
    with open('/home/shared/data/hennepin_county_parcels_geo_feat.json') as file:
        print('starting to read json file')
        hp_county_json = json.load(file)
    # make this based on selection
    selectedFeatures = []
    n_features =0
    for feat in hp_county_json['features']:
        if n_features< n :
            selectedFeatures.append(feat)
            n_features = n_features+1
    outputGeoJson = {'type': 'FeatureCollection', 'features': selectedFeatures}
    print('constructed json with selected parcels')
    outputTopoJson = tp.Topology(selectedFeatures, topology = True)
    return str(outputTopoJson)

#reads shape file and returns topojson
@app.route('/testParcels')
def getTestParcels():

   #TODO Remove hardcoded shape file

   input_shape_file ="/home/shared/data/test/map.shp"
   zipShape = zipfile.ZipFile(open(r'/home/shared/data/parcels.zip', 'rb'))
   print('read to zipshape')
   print(zipShape.namelist())
   dbfName,_, shpName,shxName = sorted(zipShape.namelist())
   print("dbfNAme:"+ dbfName+ " shpName:"+ shpName)
   reader = shapefile.Reader(shp = zipShape.open(shpName), dbf = zipShape.open(dbfName))
   # read the shapefile
   #reader = shapefile.Reader(zipshape)
   print('read to reader')
   fields = reader.fields[1:]
   
   field_names = [field[0] for field in fields]
   print(len(field_names))
   buffer = []
   i =1
   
   print(len(reader))
   batchSize = 30000

   for sr in reader.iterShapeRecords():
        
        if i % batchSize ==0:
            topojson_temp = tp.Topology(buffer, topology=True)
            topojson = tp.merge(topojson, topojson_temp)
            buffer =[]

        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buffer.append(dict(type="Feature", geometry=geom, properties=atr))
        if i%10000 ==0:
            print(i)
        i = i+1
    
   #topojson= tp.Topology(buffer, topology = True)
   topojson = tp.merge(topojson, topojson_temp)
   image = topojson.to_alt()
    #return str(topojson)
   return 'extracted json for all hennepin county parcels'
'''
MAKE YOUR OWN ROUTE:

If you added a decorator @app.route('/test')
and defined a function def test():
you can see how this works. Note: you
will need to restart the web server if you do this.

See github wiki pages for more details:
https://github.com/runck014/gems_iot_bootcamp/wiki/4.-Web-Server
'''

# route only prints data to console
@app.route('/print_data', methods=['POST'])
def print_data():
  
  print("*********************")
  print("*********************")
  print(request.method) # finds method -> here it should be "POST"
  print(request.data) # generic - get all data; covers case where you don't know what's coming
  print(request.json) # parses json data
  print("*********************")
  print("*********************")
  return "Accepted 202 - post received; printed to console"

if __name__ == "__main__":

    app.run(
     # debug=True, #shows errors 
      host='0.0.0.0', #tells app to run exposed to outside world
      #host = 'ops.parcels.com',
      #port = 80,
      port=443, #port for https
      ssl_context = ('/home/shared/hennepin_geodesign/api/server.crt','/home/shared/hennepin_geodesign/api/server.key')
      #ssl_context = context
      )

