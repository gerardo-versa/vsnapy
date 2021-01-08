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
	#print(timestamp)
	filename = "output/" + timestamp + querytype + "-" + sitename + ".txt"
	outF = open(filename, "w")
	print("SITE: " + sitename, file=outF)
	print("QUERY TYPE: " + querytype, file=outF)
	outF.close()
	return filename

def print_to_file(file, text):
	outF = open(filename, "a")	
	print(text, file=outF)
	outF.close()

def read_yaml(path):
	basic_route_url = base_url + '/api/operational/devices/device/SITE/live-status/rib/org/org/ORG/routing-instance-name/RTINAME,ipv4/route-entry-summary'
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

def read_routes():
	basic_route_url = base_url + '/api/operational/devices/device/SITE/live-status/rib/org/org/ORG/routing-instance-name/RTINAME,ipv4/route-entry-summary'
	url_list = []
	sites_check_list = []
	routes = read_yaml('routes.yaml')
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

#def get_site_names(json_text):
#	json_object = json.loads(json_text.text)
#	pairs = json_object.items()
#	for key, value in pairs:
#		for key  in value:
#			print(key.get('name'))
#			print(key.get('ipAddress'))
#print(routes())
config = read_config()
user = config['user']
password = config['password']
VD_IP = config['director-ip']

print('Director IP: ' + VD_IP + "    User: " + user + "    password: " + password)
#base_url = 'https://10.48.245.2:9182'

base_url = 'https://' + VD_IP + ':9182'

ping = check_ping()
if ping:
	url = get_url(sites())
	try:
		sites = get_data(url)
		#print(sites.text)
		Site.get_site_names(sites)
		routes_site_list = read_routes()
		for site in routes_site_list:
			sitename = site[0]
			url_list = site[1]
			print()
			print("SITE: " + sitename)
			filename = create_file("Routes",sitename)
			for url1 in url_list:
				print("!")
				print(url1)
				#print(url1[2])
				try:
					routes = get_data(url1[1])
					RoutingTable.print_routes_to_file(routes, url1[0], filename)
				except URLError:
					pdata = "Data received Site: " + sitename + " Org: "+ url1[2] + " RTI: " + url1[0] +  ", is Incorrect. Please check route.yaml file"
					print(pdata + "/n")
					print_to_file(filename, pdata)
	except AuthError:
		print("Incorrect Authentication. Please check config.yaml file")
else:
	print("VD not reachable")

