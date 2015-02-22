#!/usr/bin/env python
"""
Fetch instance information from EC2 and update zone in Route53

This script will ensure a route53 record like <instance-Name>.<my-domain>
exists for every active instance in your ec2 account. `instance-Name` refers to
the value of the 'Name' tag on each instance. If any instances have non-unique
Name tags this script will fail.

This script does not create route53 zones. You must create the zone manually
and provide the zone ID as the -z argument
"""
import boto.ec2
import route53
import argparse
import sys
import os

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', level=logging.INFO)
log = logging.getLogger('ec2_to_route53')

argp = argparse.ArgumentParser()
argp.add_argument('-r', '--region', help='Region to poll for instances.', dest='region', required=True)
argp.add_argument('-z', '--zone-id', help='Route53 zone ID to place instances into, ex: Z6J1I6EM4OQAXF', dest='zone_id', required=True)
argp.add_argument('-t', '--ttl', help='TTL for CNAME records', default=300)
argp.add_argument('-K', '--aws-access-key', help='AWS API access key', dest='aws_access_key')
argp.add_argument('-S', '--aws-secret-key', help='AWS API secret key', dest='aws_secret_key')
args = argp.parse_args()

if (args.aws_access_key is None) and ('AWS_ACCESS_KEY' in os.environ):
    args.aws_access_key = os.environ['AWS_ACCESS_KEY']
if (args.aws_secret_key is None) and ('AWS_SECRET_ACCESS_KEY' in os.environ):
    args.aws_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

ec2conn = boto.ec2.connect_to_region(args.region, aws_access_key_id=args.aws_access_key, aws_secret_access_key=args.aws_secret_key)
if ec2conn is None:
    log.fatal("Failed to connect to region: %s", args.region)
    sys.exit(1)

route53conn = route53.connect(aws_access_key_id=args.aws_access_key,
            aws_secret_access_key=args.aws_secret_key)
targetZone = route53conn.get_hosted_zone_by_id(args.zone_id)


def getEc2Instances():
    r = ec2conn.get_all_instances()
    instances = []
    for res in r:
        for ins in res.instances:
            instances.append(ins)
    if len(instances) == 0:
        log.fatal("Found 0 active ec2 instances within region: %s", args.region)
    log.info('Found %i instances', len(instances))
    return instances

def getRoute53Records():
    records = {}
    for rec in targetZone.record_sets:
        records[rec.name] = rec
    log.info('Found %i records', len(records.keys()))
    return records

instances = getEc2Instances()
records = getRoute53Records()

for instance in instances:
    if instance.state not in ('running', 'pending', 'rebooting'):
        log.debug("Skipping non-active instance %s", instance.id)
        continue
    instanceRecordName = '.'.join([instance.tags['Name'], targetZone.name]).lower()
    FQDN = '%s.' % instance.public_dns_name
    if instanceRecordName not in records:
        print instanceRecordName
        print re
        log.info("Creating new record for %s", instanceRecordName)
        new_record, change_info = targetZone.create_cname_record(
            name=instanceRecordName,
            values=[FQDN],
            ttl=args.ttl,
        )
    elif records[instanceRecordName].records[0] != FQDN:
        log.info("Updating record for %s from %s to %s", instanceRecordName, records[instanceRecordName].records[0], FQDN)
        records[instanceRecordName].records[0] = FQDN
        records[instanceRecordName].save()
    elif records[instanceRecordName].ttl != args.ttl:
        records[instanceRecordName].ttl = args.ttl
        records[instanceRecordName].save()

log.info('Processed %i instances.', len(instances))
