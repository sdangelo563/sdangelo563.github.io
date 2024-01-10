import requests
import json
import math
import folium

colors_dict = {"coal":"black","other":"gray","petroleum":"orange","natural gas":"pink","biomass":"darkgreen","geothermal":"lightgreen",\
                "hydroelectric":"darkblue","pumped storage":"blue","nuclear":"purple","solar":"white","wind":"lightblue"}

api_key = "549cBi2bKI8MRPqvcDuaEHsVSdRZyqZiCldxQxL2"

def parse_chargers():
    raw_data = requests.get("https://supercharge.info/service/supercharge/allSites").json()
    locations_file = open("supercharger_locations.txt","w+")
    for s in raw_data:
        if s['address']['country'] == 'USA' and (s['status'] == "OPEN" or s['status'] == "CLOSED_TEMP"):
            locations_file.write(str(s['gps']['latitude']) + "," + str(s['gps']['longitude']) + "," + str(s['powerKilowatt']*s['stallCount']/1000) + "\n")
    locations_file.close()

def parse_all_plants():
    locations_file = open("plant_locations.txt","w+")

    # #Contiguous 48
    for lat in range(25,55,5):
        for lon in range(-60,-130,-5):
            url_plantlist = "https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/Power_Plants_Testing/FeatureServer/0/query?where=PrimSource<>'BATTERIES' AND (Longitude >= " + \
            str(lon - 5) +" AND Longitude < " + str(lon) + ") AND (Latitude >= "+str(lat)+" AND Latitude < "+str(lat + 5)+") AND (Total_MW >= 2) &outFields=Plant_Code,PrimSource,Source,Latitude,Total_MW,Longitude&returnGeometry=false&outSR=4326&f=json"            
            raw_data = requests.get(url_plantlist).json()
            parse_plant_set(raw_data, locations_file)
            print(lat,lon)
    
    #Alaska
    url_plantlist = "https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/Power_Plants_Testing/FeatureServer/0/query?where=PrimSource<>'BATTERIES' AND (Longitude > -170 AND Longitude < -130) AND (Latitude > 50 AND Latitude < 70) AND (Total_MW >= 2) &outFields=Plant_Code,PrimSource,Source,Latitude,Total_MW,Longitude&returnGeometry=false&outSR=4326&f=json"            
    raw_data = requests.get(url_plantlist).json()
    parse_plant_set(raw_data, locations_file)
    print("Alaska")
                    
    # #Hawaii
    url_plantlist = "https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/Power_Plants_Testing/FeatureServer/0/query?where=PrimSource<>'BATTERIES' AND (Longitude > -161 AND Longitude < -154) AND (Latitude > 18 AND Latitude < 23) AND (Total_MW >= 2) &outFields=Plant_Code,PrimSource,Source,Latitude,Total_MW,Longitude&returnGeometry=false&outSR=4326&f=json"            
    raw_data = requests.get(url_plantlist).json()
    parse_plant_set(raw_data, locations_file)
    print("Hawaii")  

    #Puerto Rico
    url_plantlist = "https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/Power_Plants_Testing/FeatureServer/0/query?where=PrimSource<>'BATTERIES' AND (Longitude > -68 AND Longitude < -65) AND (Latitude > 17 AND Latitude < 19) AND (Total_MW >= 2) &outFields=Plant_Code,PrimSource,Source,Latitude,Total_MW,Longitude&returnGeometry=false&outSR=4326&f=json"            
    raw_data = requests.get(url_plantlist).json()
    parse_plant_set(raw_data, locations_file)
    print("Puerto Rico")
    
    locations_file.close()

def parse_plant_set(raw_data, locations_file):
    try:
        for p in raw_data['features']:
            url_plantdata = "https://api.eia.gov/v2/electricity/facility-fuel/data/?frequency=annual&data[0]=generation&api_key="+api_key+"&facets[plantCode][]="+str(p['attributes']["Plant_Code"])+"&facets[primeMover][]=ALL&facets[fuel2002][]=ALL&start=2022&end=2022&offset=0&length=5000"
            plantdata = requests.get(url_plantdata).json()
            try:
                if plantdata['response']['data'][0]['generation'] >= 20000 and plantdata['response']['data'][0]['generation-units'] == "megawatthours":
                    locations_file.write(str(p['attributes']['Latitude']) + "," + str(p['attributes']['Longitude']) + "," + str(p['attributes']['PrimSource']) + "," + str(plantdata['response']['data'][0]['generation']) + "\n")
                elif plantdata['response']['data'][0]['generation-units'] != "megawatthours":
                    print(plantdata['response']['data'][0]['generation-units'])
            except:
                continue
    except:
        pass

def find_plant(charger):
    source = None
    min_distance = None

    bounds = 1

    url_plantlist = "https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/Power_Plants_Testing/FeatureServer/0/query?where=PrimSource<>'BATTERIES' AND (Longitude > "+\
        str(charger[1]-bounds)+" AND Longitude < "+str(charger[1]+bounds)+") AND (Latitude > "+str(charger[0]-bounds)+" AND Latitude < "+str(charger[0]+bounds)+") AND (Total_MW >= 10) &outFields=Plant_Code,PrimSource,Source,Latitude,Total_MW,Longitude&returnGeometry=false&outSR=4326&f=json"
    raw_data = requests.get(url_plantlist).json()
    for p in raw_data['features']:
        url_plantdata = "https://api.eia.gov/v2/electricity/facility-fuel/data/?frequency=annual&data[0]=generation&api_key="+api_key+"&facets[plantCode][]="+str(p['attributes']["Plant_Code"])+"&facets[primeMover][]=ALL&facets[fuel2002][]=ALL&start=2022&end=2022&offset=0&length=5000"
        plantdata = requests.get(url_plantdata).json()
        try:
            if plantdata['response']['data'][0]['generation'] >= 20000:
                distance = math.sqrt( (charger[0]-p['attributes']['Latitude'])**2 + (charger[1]-p['attributes']['Longitude'])**2 )
                if min_distance == None or distance < min_distance:
                    min_distance = distance
                    source = p['attributes']['PrimSource']
        except:
            continue

    return source
    
def find_all_plants():
    superchargers_file = open("supercharger_locations.txt","r")
    supercharger_lines = superchargers_file.read().split("\n")[:-1]
    supercharger_string_data = [line.split(",") for line in supercharger_lines]
    supercharger_data = [[float(i) for i in line] for line in supercharger_string_data]
    superchargers_file.close()

    plant_file = open("plant_locations.txt","r")
    plant_lines = plant_file.read().split("\n")[:-1]
    plant_data = [line.split(",") for line in plant_lines]
    plant_file.close()

    final_file = open("supercharger_data.txt","w+")
    for supercharger in supercharger_data:
        source = None
        min_distance = None
        needed_energy = 24*365*supercharger[2]

        for plant in plant_data:
            if float(plant[3]) >= needed_energy:
                distance = math.sqrt( (supercharger[0]-float(plant[0]))**2 + (supercharger[1]-float(plant[1]))**2 )
                if min_distance == None or distance < min_distance:
                    min_distance = distance
                    source = plant[2]

        final_file.write(str(supercharger[0]) + "," + str(supercharger[1]) + "," + source + "\n")
    
    final_file.close()

def make_markers():
    markers_list = []
    superchargers_file = open("supercharger_data.txt","r")
    lines = superchargers_file.read().split("\n")[:-1]
    string_data = [line.split(",") for line in lines]
    for supercharger in string_data:
        markers_list.append(folium.CircleMarker(location=[float(supercharger[0]),float(supercharger[1])],radius=5,color="darkred",weight=2,fillColor=colors_dict[supercharger[2]],fill=True,fillOpacity=1))
    return markers_list

parse_chargers()
print("chargers parsed")
parse_all_plants
print("plants parsed")
find_all_plants()
print("plants found")
m = folium.Map(location=[43,-110], tiles="OpenStreetMap", zoom_start=4)
for marker in make_markers():
    marker.add_to(m)
m.save('supercharger-power-sources-2.html')
print("map generated")