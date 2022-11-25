import requests
import os
import aiptools
import logging
import argparse
import yaml
from urllib.parse import quote

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', required=True, help='The location of the configuration YAML file.')
parser.add_argument('-g', '--get_nodes', required=True, choices=['True','False'] , help='Choose whether to get new node IDs automatically or not.')
parser.add_argument('-d', '--date', required=False, help='If get_nodes is True, input a date in the form YYYYMMDD from which to search for new nodes.')
args = parser.parse_args()

logging.basicConfig(filename="create_aip.log", level=logging.INFO)

# Load config
try:
    with open(args.config, 'r') as y:
        config = yaml.safe_load(y)
except:
    logging.error("Could not open config file: " + args.config)
    raise SystemExit

larkm_url = config['larkm_host'].rstrip("/")
repo_url = config['repo_url'].rstrip("/")
auth = tuple(config['auth'])

if args.get_nodes == 'True':
    try:
        node_ids = aiptools.get_new_nodes(repo_url, args.date, auth)
        config['node_ids'] = node_ids
    except:
        logging.error("Could not retrieve node IDs.")
        raise SystemExit
else:
    node_ids = aiptools.read_config_nodes(config)

# Write node_ids to new config for use in other scripts
with open(args.config, 'w') as f:
    yaml.dump(config, f, default_flow_style=False)

# Get node.json
for node in node_ids:
    try:
        nj = aiptools.get_node_json(repo_url, str(node))
    except:
        logging.error("Could not retrieve node.json for " + str(node))
        continue
    uuid = nj['uuid'][0]['value']
    # Use node.json to fill ERC values
    try:
        who = aiptools.get_creators(repo_url, nj)
    except:
        logging.error("Manually enter ERC who for " + str(node))
        who = ":at"
    what = nj['title'][0]['value']
    when = nj['field_edtf_date_created'][0]['value']
    where = repo_url + "/node/" + str(node)
    data = {"identifier":uuid, "who":who, "what":what, "when":when, "where":where}
    p = requests.post(larkm_url, json=data)
    j = p.json()
    if p.status_code == 409:
        logging.error(j['detail'])
        if j['detail'].startswith("'where'"):
            s_url = larkm_url + "/search/?q=erc_where:" + where
        else:
            s_url = larkm_url + "/search/?q=erc_what:" + '"' + quote(what, safe='') + '"'
        s = requests.get(s_url)
        search = s.json()
        if search['num_results'] > 0:
            logging.info("ARK already exists: " + search['arks'][0]['ark_string'])
        else:
            logging.error("Could not find or create ARK for " + str(node))
            continue
    else:
        continue