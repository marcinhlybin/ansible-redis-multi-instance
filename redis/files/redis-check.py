#!/usr/bin/env python
# Redis health check for master and slave servers
# Used by consul

import sys
import argparse
import redis
from redis.exceptions import ConnectionError

parser = argparse.ArgumentParser()
type_group = parser.add_mutually_exclusive_group()
type_group.add_argument('-m', '--master', action='store_true', help='check for master'),
type_group.add_argument('-s', '--slave',  action='store_true', help='check for slave'),
parser.add_argument('host', help='redis host')
parser.add_argument('port', help='redis port')
args = parser.parse_args()

def check_master(repl):
    if repl['role'] == 'master':
        print 'OK Redis is master {}:{}'.format(redis_host, redis_port)
        sys.exit(0)
    else:
        print 'ERROR Redis is NOT master {}:{}'.format(redis_host, redis_port)
        sys.exit(2)

def check_slave(repl):
    if repl['role'] == 'slave' and repl['master_link_status'] == 'up':
        print 'OK Redis is slave {}:{}, master host {}'.format(redis_host, redis_port, repl['master_host'])
        sys.exit(0)
    elif repl['role'] == 'slave' and repl['master_link_status'] != 'up':
        print 'ERROR Redis is slave {}:{}, NOT connected to master'.format(redis_host, redis_port)
        sys.exit(2)
    else:
        print 'ERROR Redis is NOT slave {}:{}'.format(redis_host, redis_port)
        sys.exit(2)

try:
    redis_host, redis_port = args.host, args.port
    r = redis.StrictRedis(host=redis_host, port=redis_port, socket_timeout=3)
    repl = r.execute_command('INFO REPLICATION')
    repl = dict(line.split(':') for line in repl.split('\r\n') if ':' in line)
    if args.master:
        check_master(repl)
    if args.slave:
        check_slave(repl)
except ValueError:
    parser.print_help()
except ConnectionError:
    print 'ERROR Cound not connect to redis {}:{}'.format(redis_host, redis_port)
    sys.exit(2)
