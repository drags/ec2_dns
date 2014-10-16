#!/usr/bin/env python
"""Fetch instance information from AWS and update DNS"""
from tempfile import NamedTemporaryFile as tmpfile
import os
import sys
import re
import time
import subprocess
import boto.ec2
import argparse
from aws_credentials import AWS

# Let's generalize it!
argp = argparse.ArgumentParser()
argp.add_argument('-r', '--region', help='Region to poll.', dest='region', required=True)
argp.add_argument('-d', '--domain', help='(Sub)domain to be appended to AWS instance name, ex: ec2.mydomain.com', required=True)
argp.add_argument('-D', '--directory', help='Path to zone files directory', required=True, metavar='DIR')
argp.add_argument('-z', '--zone', help='Zone file name within --directory path.', required=True)
argp.add_argument('-R', '--reload-bind', help='Reload bind at end of script run', dest='reload_bind', action='store_true', default=False)
argp.add_argument('-F', '--force', help='Run as not root', action='store_true')
# TODO allow standard ENV vars for AWS API access
argp.add_argument('-K', '--aws-key', help='AWS API access key', dest='aws_key')
argp.add_argument('-S', '--aws-secret-key', help='AWS API secret key', dest='aws_secret')
args = argp.parse_args()

# Run as root
if os.getuid() != 0 and not args.force:
    print "This script must be run as root."
    sys.exit(1)

# Collect instance info from AWS API
instances = []
# TODO check for and handle auth issues
conn = boto.ec2.connect_to_region(args.region, aws_access_key_id=AWS['access_key'], aws_secret_access_key=AWS['secret_key'])
r = conn.get_all_instances()

for res in r:
    for ins in res.instances:
        instances.append(ins)

domain_zonefile_path = os.path.join(args.directory, args.zone)
if not os.path.exists(domain_zonefile_path):
    print "Unable to read domain zone file at %s" % (domain_zonefile_path)
    sys.exit(1)

hosts_include_file = os.path.join(args.directory, "instance_cnames.%s.zone" % args.domain)

print "Writing new zone include file..."
include_file = open(hosts_include_file, 'w')
for h in instances:
    if h.state not in ('running', 'pending', 'rebooting'):
        print "Skipping instances %s" % h.id
        continue
    if 'Name' not in h.tags:
        print "Got empty hostname for instance %s" % h.id
        continue
    if h.public_dns_name == '':
        print "Got empty DNS name for instance %s" % h.id
        continue

    include_file.write("%s\tIN\tCNAME\t%s.\n" % (h.tags['Name'], h.public_dns_name))

include_file.close()

zone_file = open(domain_zonefile_path, 'r')
print "Zone file path is %s" % domain_zonefile_path
print "Include file path is %s" % hosts_include_file
#sys.exit(1)
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

# Close files so that data syncs to disk
zone_file.close()
tmp_zone.close()

print 'Tmp zone is %s' % tmp_zone.name
os.rename(tmp_zone.name, zone_file.name)
os.chmod(zone_file.name, 0644)

# Allow local zone file to flush to disk
time.sleep(2)
if args.reload_bind:
    print "Reloading BIND"
    subprocess.call('service bind9 reload', shell=True)

print "Done."
