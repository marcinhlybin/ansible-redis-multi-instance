#!/usr/bin/env python
#
# Shows redis cluster status
# Usage: redis-status [-h]

import argparse
import json
import redis
import sys
import dns.resolver
from termcolor import colored

CONFIG_FILE = '/etc/redis/sentinel/cluster.json'

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', metavar='JSON', default=CONFIG_FILE, help='cluster config file ({})'.format(CONFIG_FILE))
parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='show stacktrace on error')
parser.add_argument('-n', '--nocolor', dest='nocolor', action='store_true', help='do not use colors')
parser.add_argument('-e', '--errors', dest='errors', action='store_true', help='show errors only')
parser.add_argument('masters', metavar='MASTER NAME', nargs='*', help='master name' )
args = parser.parse_args()

def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if args.debug:
        debug_hook(exception_type, exception, traceback)
    else:
        print "%s" % (exception)

sys.excepthook = exception_handler

def print_color(output, error, color):
    if args.errors and not error:
        return
    if args.nocolor:
        print output
    else:
        print colored(output, color)

with open(args.config) as f:
    config = json.load(f)

resolver = dns.resolver.Resolver()
resolver.timeout = 0.3
resolver.lifetime = 0.3

all_masters = config['redis'].keys()
if args.masters:
    masters = args.masters
    for master in masters:
        if master not in all_masters:
            raise ValueError("ERROR: Master name '{}' not found".format(master))
else:
    masters = all_masters

name_col_size = len(max(masters, key=len))
line_format = "{:<" + str(name_col_size + 2) + "} {:<8} {:<21} {:<6} {:<30}"

for redis_name in masters:
    for redis_addr in config['redis'][redis_name]:
        redis_host, redis_port = redis_addr.split(':')

        try:
            r = redis.StrictRedis(host=redis_host, port=redis_port, socket_timeout=0.3)
            repl = r.execute_command('INFO REPLICATION')
            repl = dict(line.split(':') for line in repl.split('\r\n') if ':' in line)
        except redis.exceptions.ConnectionError:
            repl = {}

        if repl.get('role') == 'master':
            output = line_format.format(redis_name, 'redis', redis_addr, repl['role'].upper(), "connected_slaves: " + repl['connected_slaves'])
            print_color(output, False, 'yellow')
        elif repl.get('role') == 'slave':
            link_status = repl['master_link_status']
            output = line_format.format(redis_name, 'redis', redis_addr, repl['role'].upper(), "master_status: " + link_status)
            if link_status == 'down':
                print_color(output, True, 'red')
            else:
                print_color(output, False, None)
        else:
            output = line_format.format(redis_name, 'redis', redis_addr, "ERROR", "")
            print_color(output, True, 'red')

    if not args.errors:
        print ""

    for sentinel_addr in config['sentinel'][redis_name]:
        sentinel_host, sentinel_port = sentinel_addr.split(':')
        r = redis.StrictRedis(host=sentinel_host, port=sentinel_port, socket_timeout=0.3)

        try:
            master_addr_by_name = r.execute_command('SENTINEL GET-MASTER-ADDR-BY-NAME {}'.format(redis_name))
        except redis.exceptions.ResponseError:
            pass
        except redis.exceptions.ConnectionError:
            master_addr_by_name = None
            pass

        if master_addr_by_name:
            master_addr = ':'.join(master_addr_by_name)
            color = None
            error = False
            try:
                ckquorum = r.execute_command('SENTINEL CKQUORUM {}'.format(redis_name))
            except redis.exceptions.ResponseError as e:
                ckquorum = str(e)
                color = 'red'
                error = True
            quorum = ' '.join(ckquorum.split(' ')[:2])
        else:
            master_addr = 'N/A'
            quorum = 'N/A'
            color = 'red'
            error = True

        output = line_format.format(redis_name, 'sentinel', sentinel_addr, "master " + master_addr, "quorum " + quorum)
        print_color(output, error, color)

    if not args.errors:
        print ""

    for role in ('master', 'slave'):
        try:
            domain = "{}.redis-{}.service.consul".format(role, redis_name)
            records = resolver.query(domain, 'A')
            message = ' '.join(sorted([record.address for record in records]))
            color = None
            error = False
        except dns.resolver.NXDOMAIN:
            color = 'red'
            error = True
            message = 'NXDOMAIN'
        except:
            color = 'red' if not args.nocolor else None
            error = True
            message = 'DNS ERROR'
        finally:
            output = line_format.format(redis_name, "dns", role, message, "")
            print_color(output, error, color)

    if not args.errors:
        print ""
