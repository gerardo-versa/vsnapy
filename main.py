import requests
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
base_url = 'https://10.48.245.2:9182'
VD_IP = "10.48.245.2"
#url = 'https://10.48.245.2:9182/api/config/nms/provider/analytics-cluster'


def get_data(url):
        raw = requests.get(url, auth=(user, password), headers={"Accept": "application/json"}, verify=False)
        return raw     

def check_ping():
    response = os.system("ping -c 1 -W 500 " + VD_IP+ " > nul")
    # and then check the response...
    if response == 0:
        return True
    else:
        return False


def sites():
	return 0

def routes():
	return 1

switcher = {
	0: base_url +  '/vnms/cloud/systems/getAllAppliancesBasicDetails?offset=0&limit=20',
	#1: 'https://10.48.245.2:9182/api/config/nms/provider/analytics-cluster',
	1: base_url + '/api/operational/devices/device/DEVICE/live-status/rib/org/org/ORG/routing-instance-name/Versa-RTINAME-VR,ipv4/route-entry-summary'
	#1: one,
	#2: two
}

def get_url(arg):
	# Get the function from switcher dictionary
	func = switcher.get(arg, "nothing")
	# Execute the function
	return func

def create_file(querytype, sitename):
	dateTimeObj = datetime.now()
	timestamp = str(dateTimeObj.year) + str(dateTimeObj.month) + str(dateTimeObj.day) + '-' + str(dateTimeObj.hour) + str(dateTimeObj.minute) + str(dateTimeObj.second) + '-'
	print(timestamp)
	filename = "output10/" + timestamp + querytype + "-" + sitename + ".txt"
	outF = open(filename, "w")
	print("SITE: " + sitename, file=outF)
	print("QUERY TYPE: " + querytype, file=outF)
	outF.close()
	return filename

def read_yaml():
	basic_route_url = base_url + '/api/operational/devices/device/SITE/live-status/rib/org/org/ORG/routing-instance-name/RTINAME,ipv4/route-entry-summary'
	url_list = []
	with open(r'config.yaml') as file:
		# The FullLoader parameter handles the conversion from YAML
		# scalar values to Python the dictionary format
		config = yaml.load(file, Loader=yaml.FullLoader)
		for sites in config.get('sites'):
			site = list(sites.keys())[0]
			for orgs in  list(sites.values()):
				for org in orgs:
					orgname = list(org.keys())[0]
					rti_list = list(org.values())[0]
					for rti in rti_list:
						print(rti)
						print(site + ' ' + orgname + ' ' + rti)
						url = basic_route_url.replace("SITE", site)
						url = url.replace("ORG", orgname)
						url = url.replace("RTINAME", rti)
						url_list.append([site, rti, url])
						print()
	return url_list

#def get_site_names(json_text):
#	json_object = json.loads(json_text.text)
#	pairs = json_object.items()
#	for key, value in pairs:
#		for key  in value:
#			print(key.get('name'))
#			print(key.get('ipAddress'))
#print(routes())

url_list = read_yaml()
for url1 in url_list:
	print(url1[2])
ping = check_ping()
if ping:
	filename = create_file("Routes","MEO-GW-001")
	url = get_url(sites())
	sites = get_data(url)
	#print(sites.text)
	Site.get_site_names(sites)
	for url1 in url_list:
		#print(url1[2])
		routes = get_data(url1[2])
		print()
		print("SITE: " + url1 [0])
		RoutingTable.print_routes_to_file(routes, url1[1], filename)
else:
	print("VD not reachable")

