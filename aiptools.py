import requests
import os
import logging

def read_config_nodes(config):
    nids = config['node_ids']
    if isinstance(nids, list):
        return nids
    elif isinstance(nids, str):
        if os.path.isfile(nids):
            try:
                with open(nids, "r") as f:
                    num_string = f.read()
                    node_ids = num_string.split(" ")
                    return node_ids
            except:
                logging.error("Could not open file: " + nids)
                raise SystemExit
        else:
            node_ids = nids.split(" ")
            return node_ids
    elif isinstance(nids, int):
        node_ids = [str(nids)]
        return node_ids
    else:
        logging.error("Could not parse node IDs in config file.")
        raise SystemExit

def get_node_json(repo_url, nid):
    n_url = repo_url + "/node/" + str(nid) + "?_format=json"
    r = requests.get(n_url)
    if r.status_code==200:
        nodejson = r.json()
        return nodejson
    else:
        logging.error("get_node_json error: invalid URL " + n_url)
        raise Warning("Invalid URL")

def get_members(repo_url, nid, user, pw):
    mem_url = repo_url + "/node/" + str(nid) + "/members?_format=json"
    r = requests.get(mem_url, auth=(user,pw))
    if r.status_code == 200:
        membersjson = r.json()
        return membersjson
    else:
        logging.error("get_members error: invalid URL or auth " + mem_url)
        raise Warning("Invalid URL or auth")

def get_field_model(url):
    r = requests.get(url)
    if r.status_code == 200:
        taxonomy = r.json()
        model = taxonomy['field_external_uri'][0]['uri']
        return model
    else:
        logging.error("get_field_model error: invalid URL " + url)
        raise Warning("Invalid URL: " + url)

# def get_new_nodes(repo_url, date, user, pw):
#     new_node_ids = []
#     pg_count = 0
#     params = {"date":date, "page":pg_count}
#     r = requests.get(repo_url + "/daily_nodes_created", params=params, auth=(user,pw))
#     if r.status_code != 200:
#         return "Could not retrieve new nodes. Status code: " + str(r.status_code)
#     new = r.json()
#     for i in range(len(new)):
#         new_node_ids.append(new[i]['nid'][0]['value'])
#     if len(new)==10:
#         next=['tmp']
#         while len(next)>0:
#             pg_count += 1
#             params['page'] = pg_count
#             r = requests.get(repo_url + "/daily_nodes_created", params=params, auth=(user, pw))
#             next = r.json()
#         if len(next) == 0:
#             return new_node_ids
#         else len(next) == 10:
#
#
#     else:
#         return new_node_ids


