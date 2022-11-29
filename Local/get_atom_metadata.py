import os
import json
import getpass
import requests

base_url = input("Enter AtoM base URL: ")
endpoint = base_url.strip("/") + "/api/informationobjects/"
slug = input("Enter AtoM slug of object: ")
user = input("Enter AtoM login email: ")
pw = getpass.getpass()

# This should be the parent folder of the object; not an individual file.
object_loc = os.path.normpath(input("Enter drive folder where object is stored: "))

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
    json.dump(j, a, indet = 4)