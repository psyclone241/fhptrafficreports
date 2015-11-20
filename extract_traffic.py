#!/usr/bin/env python
from urllib2 import urlopen
import argparse
import json
import re

try:
    from bs4 import BeautifulSoup
except ImportError as error:
    print "ImportError: " + str(error)
    print ""
    print "Have you installed BeautifulSoup?"
    print "  sudo pip install -U BeautifulSoup"
    sys.exit(1)

def main(config):
    parser = argparse.ArgumentParser(
            description=config['description'],
            epilog=''
        )
    parser.add_argument('-d', action='store', dest='data', help='Data Value: Troop Letter or County Name')
    parser.add_argument('-t', action='store', dest='type', choices=['county', 'troop'], help='Type of Search, choose "county" or "troop"')
    parser.add_argument('-o', action='store', dest='output', choices=['print', 'json'], help='Output data to the terminal with print or json (json will not include notes)')
    args = parser.parse_args()

    vars(args)

    if args.data or args.type:
        data = getCountiesAndTroops(config['county_troop_data_url'], config['data_section_id'], config['traffic_data_url'])
        if args.type:
            if args.data:
                search_value = args.data.upper()
                if args.type == 'county':
                    outputToTerminal('Looking up traffic data for ' + search_value + ' COUNTY...', args.output)
                    if search_value in data['counties']:
                        outputToTerminal('Located data, retrieving...', args.output)
                        incidents = getIncidents(data['counties'][search_value]['url'], config['traffic_data_url'], config['header_table_class'], config['incidents_table_id'], config['logo_alt_tag_attribute'])
                        outputData({ 'source': { 'url': config['county_troop_data_url'], 'type': args.type, 'county': data['counties'][search_value] }, 'data': incidents }, args.output)
                    else:
                        print 'No county by that name'
                else:
                    outputToTerminal('Lookup up traffic data for TROOP ' + search_value + '...', args.output)
                    if search_value in data['troops']:
                        outputToTerminal('Located data, retrieving...', args.output)
                        incidents = getIncidents(data['troops'][search_value]['url'], config['traffic_data_url'], config['header_table_class'], config['incidents_table_id'], config['logo_alt_tag_attribute'])
                        outputData({ 'source': { 'url': config['county_troop_data_url'], 'type': args.type,  'troop': data['troops'][search_value] }, 'data': incidents }, args.output)
                    else:
                        outputToTerminal('No troop by that letter', args.output)
            else:
                outputToTerminal('You must specify a value to search in [' + args.type + '] for', args.output)
        else:
            outputToTerminal('Choose a type (-t county or -t troop)', args.output)
    else:
        outputToTerminal('No selection made', args.output)

def outputToTerminal(data, output_format):
    if output_format == 'print':
        print data

def outputData(data, output_format):
    if output_format == 'print':
        outputToTerminal(data, output_format)
    elif output_format == 'json':
        json_data = json.dumps(data)
        print(json_data)
    else:
        print 'Invalid output format defined'

def getCountiesAndTroops(url, section_id, traffic_url):
    html = urlopen(url).read()
    if not html:
        print 'Error extracting HTML'
    soup = BeautifulSoup(html, 'lxml')
    section = soup.find('section', attrs={'id': section_id})
    table_body = section.find('tbody')
    table_rows = table_body.findAll('tr')

    first_row = table_rows[0]
    row_header = first_row.find('th')
    county_columns = row_header['colspan']

    if county_columns:
        counties = []
        troops = []
        second_row = table_rows[1]
        row_cells = second_row.findAll('td')
        row_cell_count = 1
        for row_cell in row_cells:
            if row_cell_count <= int(county_columns):
                # This will contain the table cell with X county links
                links = row_cell.findAll('a')
                for link in links:
                    link_href = link['href']
                    text = link.contents[0]
                    if traffic_url in link_href:
                        # link_href = link_href.replace(traffic_url, '')
                        # link_href = link_href.replace('.htm', '')
                        text_data = text.split(' ' + u"\u2013" + ' ')
                        counties.append( { 'url': link_href, 'name': text_data[0] })
            else:
                # This will contain the table cell with X troop links
                links = row_cell.findAll('a')
                for link in links:
                    link_href = link['href']
                    text = link.contents[0]
                    if traffic_url in link_href:
                        # link_href = link_href.replace(traffic_url, '')
                        # link_href = link_href.replace('.htm', '')
                        text_data = text.split(' ' + u"\u2013" + ' ')
                        troops.append( { 'url': link_href, 'name': text_data[0], 'headquarters': text_data[1] })
            row_cell_count+=1

        county_added_count = 0
        data = { 'troops': {}, 'counties': {} }
        for troop in troops:
            troop['id'] = troop['name'].replace('Troop ', '')
            troop['counties'] = []
            for county in counties:
                data['counties'][county['name'].upper()] = county
                if county['url'] == troop['url']:
                    county['troop'] = troop['id']
                    troop['counties'].append(county['name'])
                    county_added_count+=1
            data['troops'][troop['id'].upper()] = troop

        return data
    else:
        return None

def getIncidents(url, base_url, header_table_class, incidents_table_id, logo_alt):
    html = urlopen(url).read()
    soup = BeautifulSoup(html, 'lxml')

    incidents = { 'header': { 'logo': '', 'labels': { 'name': '', 'report': '', 'incidents_shown': '', 'service_area': '', 'last_update': { 'date': '', 'time': '', 'zone': '' } } }, 'coordinates': { 'lat': [], 'lon': [] }, 'incidents': [] }

    logoImage = soup.find('img', attrs={'alt': logo_alt})
    incidents['header']['logo'] = base_url + logoImage['src']

    headerTable = soup.find('td', attrs={'class': header_table_class})
    headerItems = []
    for element in headerTable:
        if element.string and len(element.string.strip()) > 0:
            element_stripped = element.string.strip()
            headerItems.append(element_stripped)

    labels = headerItems[0].split(' - ')
    incidents['header']['labels']['name'] = labels[0]
    incidents['header']['labels']['report'] = labels[1]
    incidents['header']['labels']['incidents_shown'] = labels[2]

    # Service Area Label
    incidents['header']['labels']['service_area'] = headerItems[1]

    # Date & Time Stamp
    dateTimeStamp = headerItems[2].split(': ')
    dateTimeStamp = dateTimeStamp[1].split(' ')
    incidents['header']['labels']['last_update']['date'] = dateTimeStamp[0]
    incidents['header']['labels']['last_update']['time'] = dateTimeStamp[1] + dateTimeStamp[2]
    zone = ''
    for i in range(3, len(dateTimeStamp)):
        zone += ' ' + dateTimeStamp[i]
    incidents['header']['labels']['last_update']['zone'] = zone.strip()

    scripts = soup.findAll('script')
    pattern_lat = re.compile('var Lat = (.*?);')
    pattern_lon = re.compile('var Lng = (.*?);')
    for script in scripts:
        if script.string:
            for line in script.string.splitlines():
                # print line.strip()
                if(pattern_lat.match(str(line.strip()))):
                    data = pattern_lat.match(line.strip())
                    incidents['coordinates']['lat'] = json.loads(data.groups()[0])
                if(pattern_lon.match(str(line.strip()))):
                    data = pattern_lon.match(line.strip())
                    incidents['coordinates']['lon'] = json.loads(data.groups()[0])

    table = soup.find('table', attrs={'id': incidents_table_id})
    table_body = table.find('tbody')

    incident_rows = table_body.findAll('tr')
    for incident_row in incident_rows:
        cells = incident_row.findAll('td')
        cells = [ele.text.strip() for ele in cells]
        cells_defined = { 'incident_type': cells[0], 'dispatch_time': cells[1], 'arrive_time': cells[2], 'county': cells[3], 'location': cells[4], 'remarks': cells[5] }
        incidents['incidents'].append(cells_defined)

    return incidents

CONFIG = {
    'traffic_data_url': 'http://www.flhsmv.gov/fhp/traffic/',
    'county_troop_data_url': 'http://www.flhsmv.gov/florida-highway-patrol/traffic-incidents-by-region/',
    'description': 'Get Traffice Reports from Florida Highway Patrol',
    'logo_alt_tag_attribute': 'Florida Highway Patrol Logo',
    'data_section_id': 'text',
    'header_table_class': 'HeaderTitle',
    'incidents_table_id': 'IncidentTable'
}

# Run the program from here
if __name__ == '__main__':
    main(CONFIG)
