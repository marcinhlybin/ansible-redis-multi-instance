#!/usr/bin/env python
#
# Check redis master address in sentinel

import argparse
import redis
import sys

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-h', '--host', metavar='HOST', default='127.0.0.1', help='sentinel host')
parser.add_argument('-p', '--port', metavar='PORT', default=26379, type=int, help='sentinel port')
parser.add_argument('-n', '--name', metavar='NAME', required=True, help='redis name')
args = parser.parse_args()

try:
    r = redis.StrictRedis(host=args.host, port=args.port, socket_timeout=0.3)
    master = r.execute_command("SENTINEL GET-MASTER-ADDR-BY-NAME {}".format(args.name))
except redis.exceptions.ConnectionError:
    print "MASTER ERROR: Sentinel '{}:{}' connection error".format(args.host, args.port)
    sys.exit(1)

if master:
    print "MASTER OK: Master for '{}' is '{}:{}'".format(args.name, master[0], master[1])
    sys.exit(0)
else:
    print "MASTER ERROR: No master for '{}' found".format(args.name)
    sys.exit(2)
