import os
import shutil
import subprocess
import sys
import bagit
import requests
import argparse
import logging

logging.basicConfig(filename="local_aip.log", level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--objects', required=True, help='The directory of objects to be bagged')
parser.add_argument('--output_dir', required=True, help='The directory where AIP bags will be saved.')
parser.add_argument('--larkm', required=True, help="The base URL of larkm.")
parser.add_argument('--fits', required=False, help="If including FITS metadata, specify the tool's location.")
args = parser.parse_args()

if os.path.exists(args.fits):
    fits = True
    fits_dir = args.fits
else:
    fits = False

def get_bag_size(bagpath):
    total = 0
    if os.path.isfile(bagpath):
        total += os.path.getsize(bagpath)
    else:
        with os.scandir(bagpath) as it:
            for obj in it:
                if obj.is_file():
                    total += obj.stat().st_size
                elif obj.is_dir():
                    total += get_bag_size(obj.path)
    if total < 1024:
        return str(total) + " bytes"
    elif total < 1024**2:
        kb=total/1024
        return str(round(kb,2)) + " KB"
    elif total < 1024**3:
        mb = total/(1024**2)
        return str(round(mb, 2)) + " MB"
    elif total < 1024**4:
        gb = total/(1024**3)
        return str(round(gb, 2)) + " GB"
    elif total < 1024**5:
        tb = total/(1024**4)
        return str(round(tb,2)) + " TB"
    else:
        pb = total/(1024**5)
        return str(round(pb,2)) + " PB"

# make a dictionary in the form of: {ark:/path/to/object}
arks_list = {}

if os.path.exists(args.objects):
    path_to_objects = args.objects
else:
    logging.error("Object file path does not exist.")
    raise SystemExit("Object file path does not exist.")

larkm_url = args.larkm.rstrip("/")
ark_lookup = larkm_url + "/search"

obj_names = os.listdir(path_to_objects)
curr = os.getcwd()
os.chdir(path_to_objects)

for name in obj_names:
    full = os.path.abspath(name)
    params = {"q":r"erc_where:"+full}
    r = requests.get(ark_lookup, params=params)
    j = r.json()
    if j['num_results'] > 0:
        ark = j['arks'][0]['ark_string']
        arks_list[ark] = full
    else:
        print("Couldn't find ARK: " + name)

os.chdir(curr)

count=1
for ark,loc in arks_list.items():
    if not os.path.exists(loc):
        print("Check file path: ", loc)
        continue
    count += 1
    uuid=ark.split("/")[1]
    bagname = os.path.join(path, uuid)
    os.mkdir(bagname)
    bagsize = get_bag_size(loc)
    info = {"Source-Organization": "Simon Fraser University",
            "Organization-Address": "8888 University Dr, Burnaby, BC V5A 1S6", "Contact-Email": "libhelp@sfu.ca",
            "External-Identifier": ark, "Internal-Sender-Identifier": loc, "Bag-Size": bagsize}
    if len(arks_list) > 1:
        info['Bag-Count'] = str(count) + " of " + str(len(arks_list))
        info['Bag-Group-Identifier'] = os.path.split(path_to_objects)[1]
    bag = bagit.make_bag(bagname, bag_info=info, checksums=['md5','sha256'])
    if os.path.isdir(loc):
        shutil.copytree(loc, os.path.join(bagname, "data"), dirs_exist_ok=True)
    elif os.path.isfile(loc):
        destpath = os.path.join(bagname, "data", os.path.basename(loc))
        shutil.copyfile(loc, destpath)
    # Get FITS metadata
    os.mkdir(os.path.join(bagname, "data", "metadata"))
    if fits is True:
        for root, subdir, files in os.walk(os.path.join(bagname, "data")):
            for file in files:
                if file.endswith("_FITS.xml"):
                    continue
                filepath = os.path.join(root,file)
                fits_filename = os.path.join(bagname, "data", "metadata", file.split(".")[0] + "_FITS.xml")
                os.chdir(fits_dir)
                if sys.platform.startswith("win"):
                    subprocess.run(["fits.bat", "-i", filepath, "-o", fits_filename])
                else:
                    subprocess.run(["fits.sh", "-i", filepath, "-o", fits_filename])
                os.chdir(curr_dir)
    bag.save(manifests=True)

#--- To-do:
#  - add descriptive metadata
#  - allow config for bag-info
