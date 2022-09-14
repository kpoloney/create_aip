import os
import requests
import argparse
import logging
import yaml

logging.basicConfig(filename="local_aip.log", level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--larkm', required=True, help="The base URL of larkm.")
parser.add_argument('--objects', required=True, help="Location of file or directory of objects to be processed.")
parser.add_argument('--single_obj', required=False, choices=['True', 'False'],
                    help="If processing a single object stored in a folder rather than a file, set to True.")
args = parser.parse_args()

if os.path.isfile(args.objects):
    objects = [args.objects]
elif args.single_obj is not None and args.single_obj==True:
    objects = [args.objects]
elif os.path.exists(args.objects):
    objects = os.listdir(args.objects)
else:
    err = "Path does not exist: " + str(args.objects)
    logging.error(err)
    raise SystemExit(err)

larkm = args.larkm.rstrip("/")
search_url = larkm + "/search/"

for item in objects:
    where = os.path.join(args.objects, item)
    if os.path.isfile(where):
        # Skip metadata file(s) on top level dir. They will be added to the bag of the object which the metadata describes.
        if item.split(".")[0].lower().endswith("_erc") or item.split(".")[0].lower().endswith("_dmd"):
            continue
        for file in objects: # Look for erc metadata file with same file name as object in question
            if file.startswith(item.split(".")[0]) and file.split('.')[0].lower().endswith("_erc"):
                erc_file = file
    elif os.path.isdir(where):
        contents = os.listdir(where)
        for part in contents:
            if part.split(".")[0].lower().endswith("_erc"):
                erc_file = part
    try:
        erc_file
    except:
        logging.warning("ERC metadata not found for: " + item + ". ARK not minted.")
        continue
    if erc_file.endswith(".txt"):
        with open(os.path.join(args.objects, erc_file), 'r') as e:
            for line in e:
                if line.startswith("who:"):
                    who = line[4:].strip()
                elif line.startswith("what:"):
                    what = line[5:].strip()
                elif line.startswith("when:"):
                    when = line[5:].strip()
        try:
            print(who, what, when)
        except:
            logging.warning(
                "Could not parse ERC elements in: " + erc_file + ". ARK not minted. Check that all required elements are present.")
            continue
    elif erc_file.lower().endswith(".yml") or erc_file.lower().endswith(".yaml"):
        with open(os.path.join(args.objects, erc_file), 'r') as y:
            erc = yaml.safe_load(y)
        try:
            who = erc['who']
            what = erc['what']
            when = erc['when']
        except:
            logging.warning(
                "Could not parse ERC elements in: " + erc_file + ". ARK not minted. Check that all required elements are present.")
            continue
    data = {'who':who, 'what':what, 'when':when, 'where':where} # TO DO: specify shoulder for local objects
    p = requests.post(larkm, json=data)
    j = p.json()
    if p.status_code == 409:
        s = requests.get(search_url, params={'q': 'erc_what:' + what})
        search = s.json()
        if search['num_results'] > 0:
            logging.info("ARK already exists: " + search['arks'][0]['ark_string'])
        else:
            logging.error("Could not find or create ARK for " + item + ". Details: " + j['detail'])
            continue