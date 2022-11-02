import os
import shutil
import subprocess
import sys
import bagit
import requests
import argparse
import logging

logging.basicConfig(filename="create_aip.log", level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--objects', required=True, help='The directory of objects to be bagged')
parser.add_argument('--output_dir', required=True, help='The directory where AIP bags will be saved.')
parser.add_argument('--larkm', required=True, help="The base URL of larkm.")
parser.add_argument('--fits', required=False, help="If including FITS metadata, specify the tool's location.")
args = parser.parse_args()

if args.fits is not None and os.path.exists(args.fits):
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
    return total

def bagsize_units(total):
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

if os.path.exists(args.objects):
    path_to_objects = args.objects
else:
    logging.error("Path to objects does not exist: " + args.objects)
    raise SystemExit("Path to objects does not exist.")

if os.path.exists(args.output_dir):
    if os.path.isdir(args.output_dir):
        output_dir = args.output_dir
    else:
        logging.error("Output directory path is not valid: " + args.output_dir)
        raise SystemExit("output_dir must be a valid directory folder.")
else:
    output_dir = os.path.join(os.getcwd(), args.output_dir)
    logging.info("Output directory not found. Creating new directory: " + output_dir)
    try:
        os.mkdir(output_dir)
    except:
        logging.error("Failed to create output directory at: " + output_dir)
        raise SystemExit("Failed to create output directory at: " + output_dir)

larkm_url = args.larkm.rstrip("/")
ark_lookup = larkm_url + "/search"
obj_names = os.listdir(path_to_objects)
curr = os.getcwd()
os.chdir(path_to_objects)

# make a dictionary in the form of: {ark:/path/to/object}
arks_list = {}
md_files = {}

for name in obj_names:
    full = os.path.abspath(name)
    if name.split(".")[0].lower().endswith("_erc") or name.split(".")[0].lower().endswith("_dmd"):
        base = name.split("_")[0]
        if name.split("_")[0] in md_files.keys():
            new = [md_files[base], full]
            md_files[base] = new
        else:
            md_files[base] = full
        continue
    params = {"q":r"erc_where:"+full}
    r = requests.get(ark_lookup, params=params)
    j = r.json()
    if j['num_results'] > 0:
        ark = j['arks'][0]['ark_string']
        arks_list[ark] = full
    else:
        logging.error("Couldn't find ARK for object: " + name)

count=0
for ark,loc in arks_list.items():
    if not os.path.exists(loc):
        logging.error("Could not find object at path: ", loc)
        continue
    uuid=ark.split("/")[1][2:]
    bagname = os.path.join(output_dir, "aip-" + uuid)
    os.mkdir(bagname)
    info = {"Source-Organization": "Simon Fraser University",
            "Organization-Address": "8888 University Dr, Burnaby, BC V5A 1S6", "Contact-Email": "libhelp@sfu.ca",
            "External-Identifier": ark, "Internal-Sender-Identifier": loc, "Validation-Date": "",
            "Source-Repository": "Special Collections and Rare Books"}
    if len(arks_list) > 1:
        info['Bag-Group-Identifier'] = os.path.split(path_to_objects)[1]
    d = requests.get(ark_lookup, params={"q":"ark_string:"+ark})
    try:
        desc = d.json()['arks'][0]['erc_what']
        info['External-Description'] = desc
    except:
        logging.info("Could not add External-Description tag for " + ark)
    bag = bagit.make_bag(bagname, bag_info=info, checksums=['md5','sha256'])
    count += 1
    if os.path.isdir(loc):
        shutil.copytree(loc, os.path.join(bagname, "data"), dirs_exist_ok=True)
    elif os.path.isfile(loc):
        destpath = os.path.join(bagname, "data", os.path.basename(loc))
        shutil.copyfile(loc, destpath)
    # Look for metadata files
    md_dir = os.path.join(bagname, "data", "metadata")
    base_name = os.path.basename(loc).split(".")[0]
    if base_name in md_files.keys():
        if not os.path.exists(md_dir):
            os.mkdir(md_dir)
        if isinstance(md_files[base_name], list):
            for md in md_files[base_name]:
                shutil.copyfile(md, os.path.join(md_dir, os.path.basename(md)))
        else:
            shutil.copyfile(md_files[base_name], os.path.join(md_dir, os.path.basename(md_files[base_name])))
    for root, subdir, files in os.walk(os.path.join(bagname,"data")):
        if "metadata" in subdir:
            subdir.remove("metadata")
        for file in files:
            tmp = os.path.splitext(file)[0].lower()
            if tmp.endswith("_fits") or tmp.endswith("_erc") or tmp.endswith("_dmd"):
                if not os.path.exists(md_dir):
                    os.mkdir(md_dir)
                os.chdir(root)
                full_loc = os.path.abspath(file)
                shutil.move(full_loc, os.path.join(md_dir, file))

    # Get FITS metadata if indicated
    if fits is True:
        if not os.path.exists(md_dir):
            os.mkdir(md_dir)
        for root, subdir, files in os.walk(os.path.join(bagname, "data")):
            if "metadata" in subdir:
                subdir.remove("metadata")
            for file in files:
                tmp = os.path.splitext(file)[0].lower()
                if tmp.endswith("_fits") or tmp.endswith("_erc") or tmp.endswith("_dmd"):
                    continue
                filepath = os.path.join(root,file)
                fits_filename = os.path.join(md_dir, file.split(".")[0] + "_FITS.xml")
                os.chdir(fits_dir)
                if sys.platform.startswith("win"):
                    subprocess.run(["fits.bat", "-i", filepath, "-o", fits_filename])
                else:
                    subprocess.run(["fits.sh", "-i", filepath, "-o", fits_filename])
    bagsize = bagsize_units(get_bag_size(os.path.join(bagname, "data")))
    bag.info['Bag-Size'] = bagsize
    bag.info['Bag-Count'] = str(count) + " of " + str(len(arks_list))
    bag.save(manifests=True)