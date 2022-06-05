#!/usr/bin/python3
import boto3
from requests import get
from getpass import getpass
from os import environ
import json
from pprint import pprint
from tabulate import tabulate
import re

security_group_id     = environ.get('AWS_SG')
region_name           = environ.get('AWS_REGION', 'eu-west-1')
aws_access_key_id     = environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = environ.get('AWS_SECRET_KEY')
ecs_cluster           = environ.get('ECS_CLUSTER', 'nsp-staging')
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




print("#\n### Instances\n#")

ec2_workers  = ec2_client.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'nsp-staging-ecs_worker',
            ]
        },
    ],
)

instance_table = [
    ['instance_id', 'Public IP']
]

for ec2_worker in ec2_workers['Reservations']:
    instance_id = ec2_worker['Instances'][0]['InstanceId']
    public_ip = ec2_worker['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
    instance_table.append([instance_id, public_ip])

print(tabulate(instance_table, headers='firstrow', tablefmt='grid', showindex=True))



print("#\n### Containers\n#")

ecs_client=boto3.client(
    'ecs',
    aws_access_key_id = aws_access_key_id,
    aws_secret_access_key = aws_secret_access_key,
    region_name = region_name
)

tasks = ecs_client.list_tasks(
    cluster=ecs_cluster
)

tasks_specs = ecs_client.describe_tasks(
    cluster=ecs_cluster,
    tasks=tasks['taskArns'],
    include=[
        'TAGS',
    ]
)

task_table = [
    ['Task', 'Status', 'Started At', 'Instance', 'CPU', 'Memory'],
]

for task in tasks_specs['tasks']:

    # Container instance
    container_instance = ecs_client.describe_container_instances(
        cluster=ecs_cluster,
        containerInstances=[task['containerInstanceArn']],
    )

    task_table.append([
        re.sub('.*\/', '', task['taskDefinitionArn']),
        task['containers'][0]['lastStatus'],
        task['startedAt'],
        container_instance['containerInstances'][0]['ec2InstanceId'],
        task['cpu'],
        task['memory'],
    ])

print(tabulate(task_table, headers='firstrow', tablefmt='grid', showindex=True))
