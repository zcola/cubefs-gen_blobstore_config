# -*- coding:utf-8 -*-
from configparser import ConfigParser
import json
import os
import sys


def read_json(filename):
    with open(filename) as f:
        json_content = json.load(f)
    return json_content


def write_json(filename, content):
    with open(filename, 'w') as f:
        f.write(content)


def gen_file(group_file):
    # 以字典的方式读取配置对象中的数据
    config = ConfigParser()

    config.read(group_file, encoding='utf-8')

    cluster_id = config['common']['CLUSTER_ID']
    log_path = config['common']['LOG_PATH']
    data_path = config['common']['DATA_PATH']

    # clustermgr
    clustermgr_dict = read_json('template/blobstore-clustermgrX.json')
    clustermgr_members_list = []
    clustermgr_http_list = []
    for clustermgr_node in eval(config['common']['CLUSTERMGR']):
        ip = clustermgr_node['ip']
        node_dict = {
            'id': clustermgr_node['id'],
            'host': '{0}:10110'.format(ip),
            'node_host': '{0}:9998'.format(ip),
            'learner': False
        }
        clustermgr_members_list.append(node_dict)
        clustermgr_http_list.append('http://{0}:9998'.format(ip))

    for clustermgr_num in range(1, 4):
        clustermgr_dict['cluster_id'] = cluster_id
        clustermgr_dict['log']['filename'] = '{0}/blobstore-clustermgr{1}.log'.format(log_path, clustermgr_num)
        clustermgr_dict['db_path'] = '{0}/blobstore-clustermgr{1}/db'.format(data_path, clustermgr_num)
        clustermgr_dict['code_mode_policies'][0]['mode_name'] = config['common']['EC_CODE_POLICIES']
        clustermgr_dict['raft_config']['server_config']['nodeId'] = clustermgr_num
        clustermgr_dict['raft_config']['server_config']['raft_wal_dir'] = '{0}/blobstore-clustermgr{1}/wal'. \
            format(data_path, clustermgr_num)
        clustermgr_dict['raft_config']['raft_node_config']['members'] = clustermgr_members_list

        os.makedirs('gen_config/' + cluster_id, exist_ok=True)
        write_json('gen_config/{0}/blobstore-clustermgr{1}.conf'.format(cluster_id, clustermgr_num),
                   json.dumps(clustermgr_dict, indent=4))

    # proxy
    proxy_dict = read_json('template/blobstore-proxy.json')
    proxy_dict['cluster_id'] = cluster_id
    proxy_dict['clustermgr']['hosts'] = clustermgr_http_list
    proxy_dict['mq']['blob_delete_topic'] = config['kafka']['blob_delete_topic']
    proxy_dict['mq']['shard_repair_topic'] = config['kafka']['shard_repair_topic']
    proxy_dict['mq']['hard_repair_priority_topic'] = config['kafka']['shard_repair_priority_topic']
    proxy_dict['mq']['msg_sender']['broker_list'][0] = config['kafka']['broker_list']
    proxy_dict['log']['filename'] = log_path + '/blobstore-proxy.log'
    write_json('gen_config/{0}/blobstore-proxy.conf'.format(cluster_id), json.dumps(proxy_dict, indent=4))

    # scheduler
    scheduler = config['common']['scheduler']
    scheduler_dict = read_json('template/blobstore-scheduler.json')
    scheduler_dict['cluster_id'] = cluster_id
    scheduler_dict['services']['members']['1'] = '{0}:9800'.format(scheduler)
    scheduler_dict['service_register']['host'] = 'http://{0}'.format(scheduler)
    scheduler_dict['clustermgr']['hosts'] = clustermgr_http_list
    scheduler_dict['blob_delete']['delete_log']['dir'] = log_path + '/blobstore-scheduler/delete_log'
    scheduler_dict['shard_repair']['orphan_shard_log']['dir'] = log_path + '/blobstore-scheduler/orphan_shard_log'
    scheduler_dict['log']['filename'] = log_path + '/blobstore-scheduler/scheduler.log'
    scheduler_dict['task_log']['dir'] = log_path + '/blobstore-scheduler/task_log'
    scheduler_dict['kafka']["blob_delete"] = {"normal": {"topic": config['kafka']['blob_delete_topic']}}
    scheduler_dict['kafka']["blob_delete"] = {"failed": {"topic": config['kafka']['blob_delete_failed_topic']}}
    scheduler_dict['kafka']["shard_repair"] = {"normal": {"topic": config['kafka']['shard_repair_topic']}}
    scheduler_dict['kafka']["shard_repair"] = {"failed": {"topic": config['kafka']['shard_repair_failed_topic']}}
    scheduler_dict['kafka']["shard_repair"] = {"priority": {"topic": config['kafka']['shard_repair_priority_topic']}}
    write_json('gen_config/{0}/blobstore-scheduler.conf'.format(cluster_id), json.dumps(scheduler_dict, indent=4))

    # blobnode
    blob_dict = read_json('template/blobstore-blobnode.json')
    blob_dict['cluster_id'] = cluster_id
    blob_dict['dropped_bid_record']['dir'] = log_path + '/blobstore-blobnode/blobnode_dropped'
    blob_dict['clustermgr']['hosts'] = clustermgr_http_list
    blob_dict['log']['filename'] = log_path + '/blobstore-blobnode/blobnode.log'
    disk_list = []
    for disk in eval(config['blobnode']['disk_path']):
        disk_info = {
            'path': disk,
            "auto_format": True,
            "max_chunks": 1024
        }
        disk_list.append(disk_info)
    blob_dict['disks'] = disk_list
    write_json('gen_config/{0}/blobstore-blobnode.conf'.format(cluster_id), json.dumps(blob_dict, indent=4))

    # access
    access_dict = read_json('template/blobstore-access.json')
    access_dict['log']['filename'] = log_path + '/blobstore-access.log'
    access_dict['stream']['cluster_config']['clusters'][0]['cluster_id'] = cluster_id
    access_dict['stream']['cluster_config']['clusters'][0]['hosts'] = clustermgr_http_list
    write_json('gen_config/{0}/blobstore-access.conf'.format(cluster_id), json.dumps(access_dict, indent=4))

    print('done!, gen in gen_config/{0}'.format(cluster_id))


if __name__ == '__main__':
    try:
        gen_file(sys.argv[1])
    except IndexError:
        print('Usage: python3 main.py groupfile.ini')
