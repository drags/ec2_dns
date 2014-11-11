#!/usr/bin/env python
"""Fetch instance information from AWS and update DNS"""
from tempfile import NamedTemporaryFile as tmpfile
import os
import sys
import re
import time
import subprocess
from chef import autoconfigure, Search
import argparse

# TODO email root in event of failure

# Let's generalize it!
argp = argparse.ArgumentParser()
argp.add_argument('-d', '--domain', help='(Sub)domain to be appended to chef node name, ex: chef.mydomain.com', required=True)
argp.add_argument('-D', '--directory', help='Path to zone files directory', required=True, metavar='DIR')
argp.add_argument('-z', '--zone', help='Zone file name within --directory path.', required=True)
argp.add_argument('-R', '--reload-bind', help='Reload bind at end of script run', dest='reload_bind', action='store_true', default=False)
argp.add_argument('-F', '--force', help='Run as not root', action='store_true')
args = argp.parse_args()

# Run as root
if os.getuid() != 0 and not args.force:
    print "This script must be run as root."
    sys.exit(1)


#############
## Get nodes
#############

# Connect to chef
chef_api = autoconfigure()

# Fetches all nodes, including down nodes. Chef doesn't know or
# care about AWS instance status. Node must be purged with knife
# to disappear from DNS
node_search = Search('node')

node_list = []

for row in node_search:
    node_list.append(row.object)

# Sort so that last seen nodes show first in list, since chef node name not
# guarenteed to be unique
node_list.sort(key=lambda x: x.get('ohai_time'), reverse=True)


#############
## Build zone file
#############

domain_zonefile_path = os.path.join(args.directory, args.zone)
# Test zone file exists
if not os.path.exists(domain_zonefile_path):
    print "Unable to read domain zone file at %s" % (domain_zonefile_path)
    sys.exit(1)

# Update CNAME include file
seen_hosts = []  # node names are not necessarily unique in chef, allow last seen to win
hosts_include_file = os.path.join(args.directory, "chef_cnames.%s.zone" % args.domain)  # TODO differentiate zonefile per node region
print "Writing new zone include file..."
include_file = open(hosts_include_file, 'w')
for node in node_list:
    try:
        node_name = node.name
    except KeyError:
        print "Did not get name for node ", node.attributes['hostname']
        continue

    if node_name.lower() in seen_hosts:
        print "Already saw a node named %s with a more recent Ohai checkin" % (node_name)
        continue
    seen_hosts.append(node_name.lower())

    if 'ec2' not in node.attributes:
        print "Did not get ec2 for node", node.attributes.keys()
        #print "Did not get ec2 for node", node.attributes['hostname']
        continue
    print "Adding node", node.name
    include_file.write("%s\tIN\tCNAME\t%s.\n" % (node.name, node.attributes['ec2']['public_hostname']))
include_file.close()

# Update Serial in parent zone file
zone_file = open(domain_zonefile_path, 'r')
print "Zone file path is %s" % domain_zonefile_path
print "Include file path is %s" % hosts_include_file
tmp_zone = tmpfile(delete=False)

while True:
    line = zone_file.readline()
    serial_match = re.match(r'(\s*)(\d+)\s*;\s*serial', line)
    if serial_match:
        new_serial = int(serial_match.group(2)) + 1
        tmp_zone.write("%s%s ; serial\n" % (serial_match.group(1), new_serial))
    else:
        tmp_zone.write(line)

    if not line:
        break

# Close and rename prior to BIND reload
zone_file.close()
tmp_zone.close()
os.rename(tmp_zone.name, zone_file.name)
os.chmod(zone_file.name, 0644)
# Allow local zone file to flush to disk
time.sleep(2)
if args.reload_bind:
    print "Reloading BIND"
    subprocess.call('service bind9 reload', shell=True)

print "Done."
