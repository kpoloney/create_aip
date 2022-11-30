import os
import json
import getpass
import requests
import argparse
from urllib.parse import urlparse

parser = argparse.ArgumentParser()
parser.add_argument('--atom_url', required=True, help='The base URL for AtoM.')
parser.add_argument('--slug', required=True, help="The AtoM slug of the object.")
parser.add_argument('--obj_dir', required=True, help="Enter parent directory of object.")
args = parser.parse_args()

def test_url(url):
    try:
        test = urlparse(url)
        return all([test.scheme, test.netloc])
    except:
        return False

if test_url(args.atom_url):
    base_url = args.atom_url.strip("/")
else:
    raise SystemExit(args.atom_url + " is not a valid URL.")

endpoint = base_url + "/api/informationobjects/"
slug = args.slug

user = input("Enter AtoM login email: ")
pw = getpass.getpass("Enter AtoM password: ")

# This should be the parent folder of the object; not an individual file.
object_loc = os.path.normpath(args.obj_dir)
if not os.path.exists(object_loc):
    raise SystemExit(object_loc + " path does not exist.")

r = requests.get(endpoint + slug, auth=(user, pw))
if r.status_code == 200:
    j = r.json()
else:
    raise SystemExit("Unable to access information object at: " + endpoint + slug)

what = j['title']
# "Authorized" is misspelled in the api response; go back and check later if this gets fixed.
who = j['creators'][0]['authotized_form_of_name']
# The date field is a RAD-compliant date and not necessarily in YYYY-MM-DD format. To get formatted, use start/end date fields
start = j['dates'][0]['start_date']
end = j['dates'][0]['end_date']
# 00 month and day are used for year-only dates in AtoM
if '-00-00' in start:
    start = start.split("-")[0]
if '00-00' in end:
    end = end.split("-")[0]
if start == end:
    when = start
else:
    when = start+"/"+end
where = object_loc

# Write data to file
erc_path = os.path.join(object_loc, slug + "_erc.txt")
with open(erc_path, 'w') as e:
    e.write("erc:\n" + "who: " + who + "\n" + "what: " + what + "\n" + "when: " + when + "\n" + "where: " + where)
md_path = os.path.join(object_loc, slug + "_atom_dmd.json")
with open(md_path, 'w') as a:
    json.dump(j, a, indent = 4)