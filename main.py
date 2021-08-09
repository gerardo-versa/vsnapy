import requests
import getpass
#import sites_list
import json
import jsondiff
import urllib3
import os
import yaml
from datetime import datetime
#from jsndiff import diff
from sites import Site
from routes import Route, RoutingTable

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
user = 'Administrator'
password = 'Versa@123$'
#base_url = 'https://10.48.245.2:9182'
#VD_IP = "10.48.245.2"
#url = 'https://10.48.245.2:9182/api/config/nms/provider/analytics-cluster'

class AuthError(Exception):
	pass

class URLError(Exception):
	pass

def get_data(url):
		raw = requests.get(url, auth=(user, password), headers={"Accept": "application/json"}, verify=False)
		if raw.status_code != 200:
			raise URLError
		return raw     

def check_ping():
    response = os.system("ping -c 4 -W 500 " + VD_IP)
    # and then check the response...
    if response == 0:
        return True
    else:
        return False

def create_file(querytype, sitename):
	dateTimeObj = datetime.now()
	timestamp = str(dateTimeObj.year) + "-" +dateTimeObj.strftime("%m") + str(dateTimeObj.day) + '-' + dateTimeObj.strftime("%H%M%S") + '-'
	#print(timestamp)
	filename = "output/" + timestamp + querytype + "-" + sitename + ".txt"
	outF = open(filename, "w")
	print("SITE: " + sitename, file=outF)
	print("QUERY TYPE: " + querytype, file=outF)
	outF.close()
	return filename

def print_to_file(filename, text):
	outF = open(filename, "a")	
	print(text, file=outF)
	outF.close()

#Method to read any yaml file
def read_yaml(path):
	url_list = []
	with open(path) as file:
		# The FullLoader parameter handles the conversion from YAML
		# scalar values to Python the dictionary format
		config = yaml.load(file, Loader=yaml.FullLoader)
	return config

def read_config():
	config = read_yaml('config.yaml')
	#print(config)
	return config

#This method reads the config from the routes.yaml file and..
# returns a list with arrays of 3 things: site name, rti name, and the url to pull the corresponding rti info
def read_routes(base_url):
	basic_route_url = base_url + '/api/operational/devices/device/SITE/live-status/rib/org/org/ORG/routing-instance-name/RTINAME,ipv4/route-entry-summary'
	url_list = []
	sites_check_list = []
	routes = read_yaml('routes.yaml')
	print(routes)
	for sites in routes.get('sites'):
		site = list(sites.keys())[0]
		#print(site)
		url_list_test = []
		for orgs in  list(sites.values()):
			for org in orgs:
				orgname = list(org.keys())[0]
				rti_list = list(org.values())[0]
				for rti in rti_list:
					#print(rti)
					#print(site + ' ' + orgname + ' ' + rti)
					url = basic_route_url.replace("SITE", site)
					url = url.replace("ORG", orgname)
					url = url.replace("RTINAME", rti)
					url_list.append([site, rti, url])
					url_list_test.append([rti,url,orgname])
		sites_check_list.append([site,url_list_test])
	#print(sites_check_list)
	return sites_check_list


#Begining of the main code
# This pulls the information from the config.yaml file and takes the inputs
config = read_config()
user = config['user']
#password = config['password']
VD_IP = config['director-ip']
#Creates a base URL that all API calls will use
base_url = 'https://' + VD_IP + ':9182'
#Checks reachability to Director
ping = check_ping()
if ping:
    password = getpass.getpass(prompt='Password for "'+ user +':')
    url = base_url + '/vnms/cloud/systems/getAllAppliancesBasicDetails?offset=0&limit=20'
	#tries to fetch the list of sites the Director has. If the request has a 400 error it assumes it is an Auth error (could be something else though, prob need to think this through)
    print(url)
    try:
        sites = get_data(url)
        #print(sites.text)
        Site.get_site_names(sites)
        routes_site_list = read_routes(base_url)
        for site in routes_site_list:
            sitename = site[0]
            url_list = site[1]
            print()
            print("SITE: " + sitename)
            filename = create_file("Routes",sitename)
            for url1 in url_list:
                print("!")
                print(url1)
				#tries to fetch the rti. If the request has a 400 error it assumes the url has incorrect information taken from the .yaml file (could be something else though, prob need to think this through)
                try:
                    routes = get_data(url1[1])
                    RoutingTable.print_routes_to_file(routes, url1[0], filename)
                except URLError:
                    pdata = "Data received Site: " + sitename + " Org: "+ url1[2] + " RTI: " + url1[0] +  ", is Incorrect. Please check route.yaml file"
                    print(pdata + "/n")
                    print_to_file(filename, pdata)
    except AuthError:
        print("Incorrect Authentication")
    except URLError:
        print("Incorrect Authentication")
else:
    print("VD not reachable")

