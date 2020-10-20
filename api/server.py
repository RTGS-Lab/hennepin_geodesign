import string
import topojson as tp
import shapefile
from json import dumps
import zipfile
from io import StringIO
import json

from flask import Flask, request

app = Flask(__name__) # setup initial flask app; gets called throughout in routes

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

@app.route('/testParcels')
def getTestParcels():

   with open('/home/shared/data/hennepin_county_parcels_topo.json') as file:
   #with open('/home/shared/data/test/output_json_1.json') as file:
       print('starting to read file')
       hp_county_topo = json.load(file)
   print('Read topo json file') 
   return 'Extracted topojson'
   
@app.route('/parcels')
def getParcels():

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
      #debug=True, #shows errors 
      host='0.0.0.0', #tells app to run exposed to outside world
      port=80)
