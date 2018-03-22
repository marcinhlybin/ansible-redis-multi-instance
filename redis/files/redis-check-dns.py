#!/usr/bin/env python
#
# Check DNS for redis domain master/slave

import argparse
import redis
import sys
import dns.resolver

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-n', '--name', metavar='NAME', required=True, help='redis name')
parser.add_argument('-r', '--role', metavar='ROLE', required=True, choices=['master', 'slave'], help='redis role')
parser.add_argument('-s', '--slaves', metavar='INT', default=3, type=int, help='number of expected slaves')
args = parser.parse_args()

resolver = dns.resolver.Resolver()
resolver.timeout = 1
resolver.lifetime = 1

try:
    domain = "{}.redis-{}.service.consul".format(args.role, args.name)
    records = resolver.query(domain, 'A')
    addr = [r.address for r in records]
except dns.resolver.NXDOMAIN:
    print "DNS ERROR: Domain '{}' not found".format(domain)
    sys.exit(2)
except Exception, e:
    print "DNS ERROR: Unknown error for domain '{}'".format(domain, e)
    sys.exit(2)

if args.role == 'slave' and len(addr) < args.slaves:
    print "DNS WARNING: Domain '{}' is missing {} slave(s)".format(domain, args.slaves - len(addr))
    sys.exit(1)

print "DNS OK: Domain '{}': {}".format(domain, ' '.join(sorted(addr)))
sys.exit(0)
