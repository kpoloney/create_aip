import argparse
import logging
import os
from urllib.parse import urlparse

logging.basicConfig(filename="validate.log", level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("--bag_dir", required=True, help="Enter the directory to bags to be validated.")
parser.add_argument("--profile_url", required=True, help="Enter the URL to the BagIt profile.")
parser.add_argument("--larkm_url", required=False, help="Include if the profile URI is an ARK indexed in larkm.")
args = parser.parse_args()

if os.path.exists(args.bag_dir):
    bag_dir = args.bag_dir
    os.chdir(bag_dir)
else:
    logging.error(args.bag_dir + " does not exist.")
    raise SystemExit(args.bag_dir + " does not exist.")

def test_url(url):
    try:
        test = urlparse(url)
        return all([test.scheme, test.netloc])
    except:
        return False

url_err_msg="Could not retrieve BagIt profile: " + args.profile_url

if urlparse(args.profile_url).scheme == 'ark':
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
else:
    if test_url(args.profile_url):
        profile_url = args.profile_url
    else:
        logging.error(url_err_msg)
        raise SystemExit(url_err_msg)

to_validate = os.listdir(bag_dir)
# Check for required metadata
for path_to_bag in to_validate:
    contents = os.listdir(os.path.join(path_to_bag, 'data'))
    erc = False
    if 'metadata' in contents:
        md = os.listdir(os.path.join(path_to_bag, 'data', 'metadata'))
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
    bag = bagit.Bag(path_to_bag)
    if bag.is_valid():
        if profile.validate_serialization(path_to_bag):
            if profile.validate(bag):
                # Add validation date to bag-info tags
                bag.info['Validation-Date'] = str(date.today())
                bag.save()
            else:
                logging.error(str(path_to_bag) + " is not valid according to BagIt Profile.")
        else:
            logging.error(str(path_to_bag) + " is not valid: serialization does not validate.")
    else:
        logging.error(str(path_to_bag) + " is invalid according to BagIt specification.")