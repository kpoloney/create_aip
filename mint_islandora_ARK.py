import requests
import os
import aiptools
import logging
import argparse
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help='The location of the configuration YAML file.')
args = parser.parse_args()

logging.basicConfig(filename="make_ARK.log", level=logging.INFO)

# Load config
try:
    with open(args.config, 'r') as y:
        config = yaml.safe_load(y)
except:
    logging.error("Could not open config file: " + args.config)
    raise SystemExit

larkm_url = config['larkm_host'].rstrip("/")
repo_url = config['repo_url'].rstrip("/")
node_ids = config['node_ids']

nids = []
if os.path.isfile(node_ids):
    try:
        with open(node_ids, "r") as f:
            num_string = f.read()
            nids.append(num_string.split(" "))
    except:
        logging.error("Could not open file: " + node_ids)
        raise SystemExit
else:
    nids.append(node_ids)

# Get node.json
for node in nids:
    nj = aips.get_node_json(repo_url, str(node))
    uuid = nj['uuid'][0]['value']
    try:
        who = nj['metatag']['value']['dcterms_creator_0']
    except KeyError:
        who = ":at"
    what = nj['title'][0]['value']
    when = nj['created'][0]['value']
    where = repo_url + "/node/" + str(node)
    data = {"identifier":uuid, "who":who, "what":what, "when":when, "where":where}
    p = requests.post(larkm_url, json=data)
    j = p.json()
    if p.status_code == 409:
        logging.error(j['detail'])
        s = requests.get(larkm_url + "/search/", params = {'q':'erc_what:'+what})
        search = s.json()
        if search['num_results'] > 0:
            logging.info("ARK already exists: " + search['arks'][0]['ark_string'])
        else:
            logging.error("Could not find or create ARK for " + str(node))
            continue