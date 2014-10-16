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
