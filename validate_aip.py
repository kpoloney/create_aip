import argparse
import logging
import os
import re
import bagit
import bagit_profile
from datetime import date
from urllib.parse import urlparse

logging.basicConfig(filename="validate.log", level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("--bag_dir", required=True, help="Enter the directory to bags to be validated.")
parser.add_argument("--profile_url", required=True, help="Enter the URL to the BagIt profile.")
parser.add_argument("--larkm_url", required=False, help="Include if the profile URI is an ARK indexed in larkm.")
parser.add_argument("--clamav", required=False, help="If using ClamAV for virus scan, enter directory of ClamAV.")
args = parser.parse_args()

if os.path.exists(args.bag_dir):
    bag_dir = args.bag_dir
else:
    logging.error(args.bag_dir + " does not exist.")
    raise SystemExit(args.bag_dir + " does not exist.")

# Check for ClamAV
if args.clamav is not None and os.path.exists(args.clamav):
    virus_check = True
    os.chdir(args.clamav)
    # Update virus database
    try:
        os.system('freshclam')
    except:
        logging.error("Could not update virus database.")
else:
    virus_check = False
    logging.info("ClamAV either not specified or unable to locate. Virus scan not completed.")

def test_url(url):
    try:
        test = urlparse(url)
        return all([test.scheme, test.netloc])
    except:
        return False

def is_ark(val):
    ark_regex = re.compile("ark:[/]?[0-9bcdfghjkmnpqrstvwxz]+/.+$")
    if ark_regex.match(val) is None:
        return False
    else:
        return True

url_err_msg = "Could not retrieve BagIt profile: " + args.profile_url

if urlparse(args.profile_url).scheme == 'ark':
    if not is_ark(args.profile_url):
        logging.error("BagIt Profile Identifier is not a valid ARK.")
    try:
        larkm = args.larkm_url.strip("/")
        params = {'q': 'ark_string:' + args.profile_url}
        s = requests.get(larkm + "/search/", params=params)
        results = s.json()
        where = results['arks'][0]['target']
        if test_url(where):
            profile_url = where
        else:
            logging.error(url_err_msg)
            raise SystemExit(url_err_msg)
    except:
        logging.error(url_err_msg)
        raise SystemExit(url_err_msg)
elif test_url(args.profile_url):
    profile_url = args.profile_url
else:
    logging.error(url_err_msg)
    raise SystemExit(url_err_msg)

to_validate = os.listdir(bag_dir)
# Check for required metadata and validate ARK
for path_to_bag in to_validate:
    contents = os.listdir(os.path.join(bag_dir, path_to_bag, 'data'))
    try:
        with open(os.path.join(bag_dir, path_to_bag, "bag-info.txt"), 'r') as b:
            for line in b:
                if line.startswith("External-Identifier: "):
                    ext_id = line.split(": ")[1].strip()
                    if urlparse(ext_id).scheme == 'ark':
                        ark = ext_id
                        break
            if not is_ark(ark):
                logging.error("Could not validate ARK for: ", path_to_bag)
    except:
        logging.error("Could not validate ARK for: ", path_to_bag)
    erc = False
    if 'metadata' in contents:
        md = os.listdir(os.path.join(bag_dir, path_to_bag, 'data', 'metadata'))
        for file in md:
            name = os.path.splitext(file)[0].lower()
            if name.endswith("_erc"):
                erc = True
                break
    else:
        for file in contents:
            name = os.path.splitext(file)[0].lower()
            if name.endswith("_erc"):
                erc = True
                break
    if not erc:
        logging.error(str(path_to_bag) + " is not a valid AIP: ERC metadata file not found.")
        continue

# Validate the AIP against BagIt specification and BagIt profile
profile = bagit_profile.Profile(profile_url)
for path_to_bag in to_validate:
    os.chdir(bag_dir)
    bag = bagit.Bag(path_to_bag)
    if bag.is_valid():
        if profile.validate_serialization(path_to_bag):
            if profile.validate(bag):
                # Add validation date to bag-info tags
                bag.info['Validation-Date'] = str(date.today())
                bag.save(manifests=True)
            else:
                logging.error(str(path_to_bag) + " is not valid according to BagIt Profile.")
        else:
            logging.error(str(path_to_bag) + " is not valid: serialization does not validate.")
    else:
        logging.error(str(path_to_bag) + " is invalid according to BagIt specification.")
    # Virus scan
    if virus_check is True:
        os.chdir(args.clamav)
        logpath = os.path.join(bag_dir, path_to_bag, "data", "metadata", "clamav_scan.txt ")
        cmd = "clamscan -ri --log=" + logpath + " " + os.path.join(bag_dir, path_to_bag)
        os.system(cmd)
        bag.info["Virus-Scan-Date"] = str(date.today())
        bag.info["Virus-Scan-Software"] = "ClamAV"
        with open(logpath, 'r') as s:
            for line in s:
                if line.startswith("Infected"):
                    inf = int(line.split(": ")[1])
                    if inf > 0:
                        logging.error("Infected file(s) found in bag: " + path_to_bag + ". See clamav_scan.txt for more information.")
                if line.startswith("Engine version"):
                    bag.info['Virus-Scan-Software-Version'] = line.split(": ")[1]
        bag.save(manifests=True)