#!/usr/bin/env python
#
# Consul status
# Shows agent, checks and DNS information
#
# Usage: consul-status [-l] [-c /etc/consul/consul.json]
#
import consulate
import argparse
import json
import sys
import dns.resolver
from termcolor import colored

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--consul-config', default="/etc/consul/consul.json", help='consul config file')
parser.add_argument('-l', '--local-resolver', action='store_true', help='use local resolver (/etc/resolv.conf)')
args = parser.parse_args()

try:
    with open(args.consul_config) as f:
        config = json.load(f)
        consul_host = config['bind_addr']
        consul_port = config['ports']['http']
        consul_domain = config['domain']
        consul_dns_port = config['ports']['dns']

    resolver = dns.resolver.Resolver()
    resolver.timeout = 0.5
    resolver.lifetime = 0.5

    if not args.local_resolver:
        resolver.nameservers = [consul_host]
        resolver.port = consul_dns_port

    consul = consulate.Consul(host=consul_host, port=consul_port)
    services = consul.agent.services()[0]
    checks = consul.agent.checks()[0]
    del services['consul']

    # Agents
    for name, service in sorted(services.items()):
        tags = ', '.join(service['Tags'])
        redis = "{}:{}".format(service['Address'], str(service['Port']))
        print "{:<30} {:<6} {:<20} {:<40}".format(name, 'agent', 'tags ' + tags, redis)

    print

    # Checks
    for name, check in sorted(checks.iteritems()):
        name = check['ServiceName']
        status = check['Status']
        output = check['Output'].strip()

        if status != 'passing':
            line = "{:<30} {:<6} " + colored("{:<20}", 'red') + " {:<45}"
        else:
            line = "{:<30} {:<6} {:<20} {:<45}"

        print line.format(name, 'check', 'status ' + status, 'output ' + output)

    print

    # DNS
    for name, service in sorted(services.items()):
        for tag in service['Tags']:
            try:
                domain = "{}.{}.service.consul".format(tag, name)
                records = resolver.query(domain, 'A')
                output = ' '.join(sorted([record.address for record in records]))
            except dns.resolver.NXDOMAIN:
                output = colored('NXDOMAIN', 'red')
            except:
                output = colored('DNS ERROR', 'red')
            finally:
                print "{:<30} {:<6} {:<20} {:<30}".format(name, 'dns', tag, output)

except Exception, e:
    print e
    sys.exit(2)
