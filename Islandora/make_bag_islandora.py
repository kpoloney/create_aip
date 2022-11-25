import os
import sys
import argparse
import logging
import yaml
import aiptools

logging.basicConfig(filename="create_aip.log", level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help='The location of the configuration YAML file.')
parser.add_argument('--bagger_dir', required=True, help='Path to Islandora bagger directory')
parser.add_argument('--bagger_config', required=False, help='Location of the Islandora bagger configuration file.')
args = parser.parse_args()

# Load aip config
try:
    with open(args.config, 'r') as y:
        config = yaml.safe_load(y)
except:
    logging.error("Could not open config file: " + args.config)
    raise SystemExit("Could not open config file.")

try:
    t = os.path.exists(args.bagger_dir)
    if t is True:
        bagger_dir = args.bagger_dir
    else:
        logging.error("Directory does not exist: "+ args.bagger_dir)
        raise SystemExit("Could not access Islandora bagger directory.")
except:
    logging.error("Could not access Islandora bagger directory.")
    raise SystemExit("Could not access Islandora bagger directory")

# Check for METS files
try:
    mets = config['mets_dir']
except:
    logging.warning("METS metadata not found.")
    mets = False

repo_url = config['repo_url'].rstrip("/")
larkm_url = config['larkm_url'].rstrip("/")

# Load bagger config
try:
    with open(args.bagger_config, 'r') as y:
        bagger_config = yaml.safe_load(y)
        config_loc = args.bagger_config
except:
    config_loc = os.path.join(args.config, "bagger_config.yml")
    logging.warning("Could not open config file: " + args.bagger_config)
    logging.info("Creating default bagger config file.")
    # Basic baginfo tags (add bagit profile id once assigned)
    baginfo = {'BagIt-Profile-Identifier': '',
               'Source-Organization': 'Simon Fraser University',
               'Organization-Address': '8888 University Dr, Burnaby, BC V5A 1S6',
               'Contact-Email': 'libhelp@sfu.ca'}
    bagger_config = {'drupal_base_url':config['repo_url'],
                     'drupal_basic_auth':config['auth'],
                     'bag_name':'uuid',
                     'bag_name_template':'aip-%',
                     'temp_dir':'/tmp/islandora_bagger_temp',
                     'output_dir':'/tmp',
                     'serialize':'false',
                     'log_bag_creation': 'true',
                     'plugins':['AddBasicTags', 'AddNodeJson','AddFileFromTemplate'],
                     'bag-info':baginfo,
                     'hash_algorithm': ['md5', 'sha256', 'sha512'],
                     'drupal_media_tags': [],
                     'include_media_use_list': True,
                     'template_path': 'templates/dc.twig',
                     'templated_output_filename': 'metadata/DublinCore_dmd.xml'
    }

node_ids = aiptools.read_config_nodes(config)
for nid in node_ids:
    # Add METS fname to files_to_add config option (NodeId_METS.xml)
    if mets:
        mets_file = os.path.join(mets, str(nid) + '_mets.xml')
        if os.path.exists(mets_file):
            bagger_config['plugins'].append("AddFile")
            bagger_config['files_to_add'] = mets_file
        else:
            logging.info("No METS file found for node: " + str(nid))
    # Add node-specific bag-info tags
    ark = aiptools.get_ark(larkm_url, repo_url, nid)
    bagger_config['bag-info']['External-Identifier'] = ark
    d = requests.get(larkm_url+"/search/", params={"q":"ark_string:"+ark})
    try:
        descr=d.json()['arks'][0]['erc_what']
        bagger_config['bag-info']['External-Description'] = descr
    except:
        logging.info("Could not add External-Description tag for node: "+str(nid))
    bagger_config['bag-info']['Internal-Sender-Identification'] = repo_url + "/node/" + str(nid)
    if "summit" in repo_url:
        bagger_config['bag-info']['Source-Repository'] = "Summit Research Repository"
    # Write edited config to file
    with open(config_loc, 'w') as b:
        yaml.dump(bagger_config, default_flow_style=False)
    # Run Islandora bagger with given configuration for each node ID
    os.chdir(bagger_dir)
    fname = os.path.basename(config_loc)
    if sys.platform.startswith("win"):
        cmd = "php bin\console app:islandora_bagger:create_bag --settings=" + fname + " --node=" + str(nid)
    else:
        cmd = "./bin/console app:islandora_bagger:create_bag --settings=" + fname + " --node=" + str(nid)
    os.system(cmd)