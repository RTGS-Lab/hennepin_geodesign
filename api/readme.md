# Hennepin County Geo Design - Server side API

The server side APIs support client requests to select parcels, save and retrieve parcel designs from database

## List of APIs exposed
### 1. Select Parcels
API to choose required parcels from database based on water quality index, habitatt quality index, parcel type etc
    
    http://localhost:80/parcels?n=10&watqual_c=68&watqual_nc=52&habQual_c=41&habQual_nc=53&pr_typ_nm1=RESIDENTIAL
    
### 2. Save Parcel design
API to save parcel design communicated by client 
    
It saves to parcel_design table in the database
    
    http://localhost:80/save with design json in the request arguments
    
 ### 3. Retrieve Parcel design
API to load parcel design from the database given design name, group name or both   

    http://localhost:80/load?designName=design1
    
    http://localhost:80/load?groupName=group_344
    
    http://localhost:80/load?designName=design_123&groupName=group_344
    
### 4. Retrieve Parcel design summary
API to load summary of parcel design for a user id. It is light weight when compared to *'load'* API
    
    http://localhost:80/loadSummary?userId=1
    
*Actual ip address of the server not published for privacy reasons*
