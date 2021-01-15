import requests
import json
import urllib3
import os
import yaml
from datetime import datetime
from sites import Site
from routes import Route, RoutingTable
from pathlib import Path


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AuthError(Exception):
    pass

class URLError(Exception):
    pass

def get_data(url: str):
        raw = requests.get(url, auth=(user, password), headers={"Accept": "application/json"}, verify=False)
        if raw.status_code != 200:
            raise URLError
        return raw

def check_ping():
    response = os.system(f"ping -c 4 -W 500 {VD_IP}")
    return not response

def create_file(querytype: str, sitename: str) -> Path:
    dateTimeObj = datetime.now()
    timestamp = dateTimeObj.strftime("%Y-%m-%d-%H%M%S")
    #print(timestamp)
    filename = Path(f"output/{timestamp}-{querytype}-{sitename}.txt")
    with filename.open("w") as outF:
        print("SITE: " + sitename, file=outF)
        print("QUERY TYPE: " + querytype, file=outF)
    return filename

def append_to_file(filename, text):
    with filename.open("a"):
        filename.write(text)


def read_routes(base_url):
    basic_route_url = f'{base_url}/api/operational/devices/device/SITE/live-status/rib/org/org/ORG/routing-instance-name/RTINAME,ipv4/route-entry-summary'
    url_list = []
    sites_check_list = []
    routes = yaml.load(Path('routes.yaml').open(), Loader=yaml.FullLoader)
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


config = yaml.load(Path('config.yaml').open(), Loader=yaml.FullLoader)
user = config['user']
password = config['password']
VD_IP = config['director-ip']

print(f'Director IP: {VD_IP}    User: {user}    password: {password}')

base_url = f'https://{VD_IP}:9182'

ping = check_ping()
if ping:
    url = f'{base_url}/vnms/cloud/systems/getAllAppliancesBasicDetails?offset=0&limit=20'
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
            filename = create_file("Routes", sitename)
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
                    append_to_file(filename, pdata)
    except AuthError:
        print("Incorrect Authentication. Please check config.yaml file")
else:
    print("VD not reachable")

