#!/usr/bin/python3
import boto3
from requests import get
from getpass import getpass
from os import environ
import json


security_group_id     = environ.get('AWS_SG')
region_name           = environ.get('AWS_REGION')
aws_access_key_id     = environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = environ.get('AWS_SECRET_KEY')
ports=json.loads(environ.get('ports', []))

aws_secret_access_key = getpass('AWS_SECRET_KEY:')

ec2_client=boto3.client(
    'ec2',
    aws_access_key_id = aws_access_key_id,
    aws_secret_access_key = aws_secret_access_key,
    region_name = region_name
)

security_groups=ec2_client.describe_security_groups(GroupIds=[security_group_id])
security_groups=security_groups['SecurityGroups']

# Revoking existing ingress
if len(security_groups) > 0:
    for sg in security_groups:
        IpPermissions=sg['IpPermissions']
        if len(IpPermissions) > 0:
            for perm in IpPermissions:
                print("Revoking {}".format(perm))
                ec2_client.revoke_security_group_ingress(GroupId=sg['GroupId'],IpPermissions=[perm])

# Setting new rule
ip = get('https://api.ipify.org').content.decode('utf8')
print('My public IP address is: {}'.format(ip))
for port in ports:
    ec2_client.authorize_security_group_ingress(GroupId=security_groups[0]['GroupId'],IpPermissions=[
    {
        'FromPort': port['port'],
        'IpProtocol': port['protocol'],
        'IpRanges': [
            {
                'CidrIp': ip + '/32',
                'Description': 'Set by automated script'
            },
        ],
        'ToPort': port['port'],
    },
    ])
    print("Added port {}/{} from IP {}".format(port['port'], port['protocol'], ip))
