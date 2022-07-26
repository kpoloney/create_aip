import requests
import os
import aiptools
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--larkm_url", required=True, help="larkm host URL." )
parser.add_argument("--repo_url", required=False, help="Base URL of Islandora repository")
parser.add_argument("--filename", required=False, help="Location of text file or a space separated list of node ids.")
args = parser.parse_args()

logging.basicConfig(filename="make_ARK.log", level=logging.INFO)

# larkm_url = input("Enter larkm host: ").rstrip("/")
# repo_url = input("Enter Islandora repository URL: ").rstrip("/")
# fn = input("Enter list of node IDs (txt file or space-separated list): ") # Double check format; may be space separated.

nids = []
if os.path.isfile(args.filename):
    try:
        with open(args.filename, "r") as f:
            for line in f:
                nids.append(line.strip())
    except:
        logging.error("Could not open " + args.filename)
else:
    for n in args.filename.split(" "):
        nids.append(n.strip())

# Get node.json
for node in nids:
    nj = aips.get_node_json(args.repo_url.rstrip("/"), str(node))
    uuid = nj['uuid'][0]['value']
    try:
        who = nj['metatag']['value']['dcterms_creator_0']
    except KeyError:
        who = ":at"
    what = nj['title'][0]['value']
    when = nj['created'][0]['value']
    where = args.repo_url.rstrip("/") + "/node/" + str(node)
    data = {"identifier":uuid, "who":who, "what":what, "when":when, "where":where}
    p = requests.post(args.larkm_url.rstrip("/"), json=data)
    j = p.json()
    if p.status_code == 409:
        logging.error(j['detail'])
        s = requests.get(args.larkm_url.rstrip("/")+"/search/", params = {'q':'erc_what:'+what})
        search = s.json()
        if search['num_results'] > 0:
            logging.info("ARK already exists: " + search['arks'][0]['ark_string'])
        else:
            logging.error("Could not find or create ARK for " + str(node))
            continue