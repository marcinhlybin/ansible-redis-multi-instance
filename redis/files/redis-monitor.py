#!/usr/bin/env python
#
# Sentinel monitor
# Registers master/slave redis servers in consul based on sentinels output
#
# It runs periodically from systemd
#
# Usage:
# sentinel-monitor [-c /etc/redis/sentinel/monitor.conf]

import redis
import argparse
import time
import sys
import netifaces
import consulate
import os
import ConfigParser
import logging

CONFIG_FILE = '/etc/redis/monitor/monitor.conf'

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', metavar='FILE', default=CONFIG_FILE, help='config file path, default {}'.format(CONFIG_FILE))
parser.add_argument('-d', '--deregister', metavar='NAME', help='deregister service from consul')
args = parser.parse_args()

config_file = args.config
config = ConfigParser.ConfigParser(allow_no_value=True)
config.read(config_file)

consul_address = config.get('global', 'consul')
consul_host, consul_port = consul_address.split(':')

check_interval = int(config.get('global', 'check_interval'))
log_file = config.get('global', 'log_file')
log_level = config.get('global', 'log_level')
redis_servers = config.items('redis')
sentinel_servers = config.items('sentinels')

logging.basicConfig(filename=log_file, format='%(asctime)s %(message)s', level=log_level)

class ConnectionError(Exception):
    pass

def master_for(redis_name):
    for sentinel_host, sentinel_port in sentinel_servers:
        try:
            s = redis.StrictRedis(sentinel_host, sentinel_port, socket_timeout=3)
            quorum = s.execute_command('SENTINEL CKQUORUM', redis_name)
            if not quorum.startswith('OK'):
                continue

            redis_master = s.execute_command('SENTINEL GET-MASTER-ADDR-BY-NAME', redis_name)
            return redis_master

        except Exception, e:
            logging.info("Sentinel error: {}".format(e))
            broken_server = sentinel_servers.pop(0)
            sentinel_servers.append(broken_server)
            continue

    raise ConnectionError('Could not connect to sentinels or no quorum')

def consul_register(redis_name, master_host, redis_address):
    redis_host, redis_port = redis_address.split(':')

    if master_host == redis_host:
        logging.info("Register master {} {}".format(redis_name, redis_address))
        consul.agent.service.register(
            name='redis-' + redis_name,
            address=redis_host,
            port=int(redis_port),
            tags=['master'],
            check="/usr/local/sbin/redis-check --master {} {}".format(redis_host, redis_port),
            interval=str(check_interval) + 's'
        )
    else:
        logging.info("Register slave {} {}".format(redis_name, redis_address))
        consul.agent.service.register(
            name='redis-' + redis_name,
            address=redis_host,
            port=int(redis_port),
            tags=['slave'],
            check="/usr/local/sbin/redis-check --slave {} {}".format(redis_host, redis_port),
            interval=str(check_interval) + 's'
        )

    return

def consul_deregister(redis_name):
    logging.info("Deregister {}".format(redis_name))
    consul.agent.service.deregister(redis_name)

def sentinel_deregister(redis_name):
    for sentinel_host, sentinel_port in sentinel_servers:
        try:
            s = redis.StrictRedis(sentinel_host, sentinel_port, socket_timeout=3)
            s.execute_command('SENTINEL REMOVE', redis_name)
            return
        except:
            continue

try:
    logging.debug("Connect to consul {}".format(consul_address))
    consul = consulate.Consul(consul_host, consul_port)

    if args.deregister:
        redis_name = args.deregister
        consul_deregister('redis-' + redis_name)
        sentinel_deregister(redis_name)
    else:
        for redis_name, redis_address in redis_servers:
            master_host, master_port = master_for(redis_name)
            consul_register(redis_name, master_host, redis_address)
except Exception, e:
    logging.warning("Error {}: {}".format(redis_name, e))
