# Multi instance replicated Redis with DNS support

Features:

* multi instance Redis support
* master-slave replication: one master, many slaves
* failover support with redis sentinel
* master discovery and DNS with consul
* custom-built redis monitor with quorum checking to register services in consul
* status screens: `redis-status` and `consul-status`

Tested with Redis 4.0.2 and Consul 0.7.2 on Debian Stretch.
This code is not maintained. If you like my roles feel free to copy and adjust to your needs.

**Note:** Consul works as a DNS recursor. Normally you would like to have a DNS server such as Bind9 and configured forwarder to consul servers for `.consul` domain.

## Vagrant installation

```
cd vagrant
vagrant up
ansible-playbook playbooks/site.yml
```

*Deployment takes around 10 minutes*

## Status screens

### redis-status

Log in to any server and run `redis-status` to see status of all instances or `redis-status test1` for only one. All servers show the same output. Use `redis-status -e` to show errors.

```
$ ssh 192.168.44.11 -l vagrant

vagrant@redis1:~$ redis-status
test1   redis    192.168.44.11:3010    MASTER connected_slaves: 3
test1   redis    192.168.44.12:3010    SLAVE  master_status: up
test1   redis    192.168.44.13:3010    SLAVE  master_status: up
test1   redis    192.168.44.14:3010    SLAVE  master_status: up

test1   sentinel 192.168.44.11:26379   master 192.168.44.11:3010 quorum OK 4
test1   sentinel 192.168.44.12:26379   master 192.168.44.11:3010 quorum OK 4
test1   sentinel 192.168.44.13:26379   master 192.168.44.11:3010 quorum OK 4
test1   sentinel 192.168.44.14:26379   master 192.168.44.11:3010 quorum OK 4

test1   dns      master                192.168.44.11
test1   dns      slave                 192.168.44.12 192.168.44.13 192.168.44.14

test3   redis    192.168.44.11:3030    SLAVE  master_status: up
test3   redis    192.168.44.12:3030    MASTER connected_slaves: 3
test3   redis    192.168.44.13:3030    SLAVE  master_status: up
test3   redis    192.168.44.14:3030    SLAVE  master_status: up

test3   sentinel 192.168.44.11:26379   master 192.168.44.12:3030 quorum OK 4
test3   sentinel 192.168.44.12:26379   master 192.168.44.12:3030 quorum OK 4
test3   sentinel 192.168.44.13:26379   master 192.168.44.12:3030 quorum OK 4
test3   sentinel 192.168.44.14:26379   master 192.168.44.12:3030 quorum OK 4

test3   dns      master                192.168.44.12
test3   dns      slave                 192.168.44.11 192.168.44.13 192.168.44.14

test2   redis    192.168.44.11:3020    MASTER connected_slaves: 3
test2   redis    192.168.44.12:3020    SLAVE  master_status: up
test2   redis    192.168.44.13:3020    SLAVE  master_status: up
test2   redis    192.168.44.14:3020    SLAVE  master_status: up

test2   sentinel 192.168.44.11:26379   master 192.168.44.11:3020 quorum OK 4
test2   sentinel 192.168.44.12:26379   master 192.168.44.11:3020 quorum OK 4
test2   sentinel 192.168.44.13:26379   master 192.168.44.11:3020 quorum OK 4
test2   sentinel 192.168.44.14:26379   master 192.168.44.11:3020 quorum OK 4

test2   dns      master                192.168.44.11
test2   dns      slave                 192.168.44.12 192.168.44.13 192.168.44.14

test4   redis    192.168.44.11:3040    SLAVE  master_status: up
test4   redis    192.168.44.12:3040    MASTER connected_slaves: 3
test4   redis    192.168.44.13:3040    SLAVE  master_status: up
test4   redis    192.168.44.14:3040    SLAVE  master_status: up

test4   sentinel 192.168.44.11:26379   master 192.168.44.12:3040 quorum OK 4
test4   sentinel 192.168.44.12:26379   master 192.168.44.12:3040 quorum OK 4
test4   sentinel 192.168.44.13:26379   master 192.168.44.12:3040 quorum OK 4
test4   sentinel 192.168.44.14:26379   master 192.168.44.12:3040 quorum OK 4

test4   dns      master                192.168.44.12
test4   dns      slave                 192.168.44.11 192.168.44.13 192.168.44.14
```

### consul-status

Log in to the server as root and run `consul-status`. It shows agent, checks and DNS information. Each server shows different output.

```
vagrant@redis1:~$ sudo -i
root@redis1:~# consul-status
redis-test1                    agent  tags master          192.168.44.11:3010
redis-test2                    agent  tags master          192.168.44.11:3020
redis-test3                    agent  tags slave           192.168.44.11:3030
redis-test4                    agent  tags slave           192.168.44.11:3040

redis-test1                    check  status passing       output OK Redis is master 192.168.44.11:3010
redis-test2                    check  status passing       output OK Redis is master 192.168.44.11:3020
redis-test3                    check  status passing       output OK Redis is slave 192.168.44.11:3030, master host 192.168.44.12
redis-test4                    check  status passing       output OK Redis is slave 192.168.44.11:3040, master host 192.168.44.12

redis-test1                    dns    master               192.168.44.11
redis-test2                    dns    master               192.168.44.11
redis-test3                    dns    slave                192.168.44.11 192.168.44.13 192.168.44.14
redis-test4                    dns    slave                192.168.44.11 192.168.44.13 192.168.44.14
```
