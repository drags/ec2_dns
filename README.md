# EC2 to BIND
Simple tool to maintain consistency between what's alive in EC2 and what's listed by your named server.

## Usage
    usage: ec2_to_bind_zone.py [-h] -r REGIONS -d DOMAIN -D DIRECTORY -z ZONE [-R] [-F] [-K AWS_KEY] [-S AWS_SECRET]

    optional arguments:
      -h, --help                            show this help message and exit
      -r REGION, --region REGION            Region to poll.
      -d DOMAIN, --domain DOMAIN            (Sub)domain to be appended to AWS instance name, ex: ec2.mydomain.com
      -D DIR, --directory DIR               Path to zone files directory
      -z ZONE, --zone ZONE                  Zone file name within --directory path.
      -R, --reload-bind                     Reload bind at end of script run
      -F, --force                           Run as a non root user
      -K KEY, --aws-key KEY                 AWS API access key
      -S SECRET, --aws-secret-key SECRET    AWS API secret key

## Bind config

This script is designed to maintain a BIND zone include file containing CNAMES to ec2 "public dns name"s. While the script can increment the zone file serial and reload bind (with the -R option), it will not edit your zone file to make it properly formatted. Refer to the test/ec2.example.com.zone file (specifically the $ORIGIN and $INCLUDE lines) for an example of a correct setup. Essentially the generated "instance_cnames.<domain>.zone" file must be included by the "parent" zone file, _after_ a correct $ORIGIN line has been specified.

## Disclaimer

This tool is brand new, please holler at the [issues](https://github.com/drags/ec2_dns/issues) page for any funkyness that arises.

Which is a perfect segue to..

## Warranty

**NONE.**

This software may blow up all of your zone files, your computer, and possibly your face. Use at your own risk!
