#!/usr/bin/env python
#
# Check quorum for sentinels

import argparse
import redis
import sys

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-h', '--host', metavar='HOST', default='127.0.0.1', help='sentinel host')
parser.add_argument('-p', '--port', metavar='POST', default=26379, type=int, help='sentinel port')
parser.add_argument('-n', '--name', metavar='name', required=True, help='redis name')
args = parser.parse_args()

try:
    r = redis.StrictRedis(host=args.host, port=int(args.port), socket_timeout=0.3)
    ckquorum = r.execute_command("SENTINEL CKQUORUM {}".format(args.name))
except redis.exceptions.ConnectionError:
    print "QUORUM ERROR: Sentinel '{}:{}' connection error".format(args.host, args.port)
    sys.exit(1)
except redis.exceptions.ResponseError, e:
    print "QUORUM ERROR: Redis '{}': {}".format(args.name, str(e))
    sys.exit(2)

print "QUORUM OK: Redis '{}': {}".format(args.name, ckquorum)
sys.exit(0)
