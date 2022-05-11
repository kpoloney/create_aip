import os
import shutil
import subprocess
import sys
import bagit

# Path to where bag dir(s) will be made
path = input("Enter directory to save bags: ")
try:
    os.path.exists(path)
except:
    print("Path does not exist.")

# Where is fits saved? 
fits_dir = input("Enter directory where FITS is saved: ")
try:
    os.path.exists(os.path.join(fits_dir, "fits.bat"))
except:
    print("Couldn't find FITS.")

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

# ideally, we will have (or be able to get) a dictionary in the form of: {ark:/path/to/object}
arks_list = {}

# If we don't have the objects loc already, need to create arks_list
# path_to_objects = input("Enter directory of objects: ")
# obj_names = os.listdir(path_to_objects)
# for name in obj_names:
#     # check if it has an ark -- somehow?
#     # add ark to dict
#     arks_list[ark] = os.path.join(path_to_objects, name)

curr_dir = os.getcwd()

count=1
for ark,loc in arks_list.items():
    if not os.path.exists(loc):
        print("Check file path: ", loc)
        continue
    count += 1
    uuid=ark.split("/")[2]
    bagname = os.path.join(path, uuid)
    os.mkdir(bagname)
    bagsize = get_bag_size(loc)
    info = {"Source-Organization": "Simon Fraser University",
            "Organization-Address": "8888 University Dr, Burnaby, BC V5A 1S6", "Contact-Email": "summit@sfu.ca",
            "External-Identifier": ark, "Internal-Sender-Identifier": loc, "Bag-Size": bagsize}
    if len(arks_list) > 1:
        info['Bag-Count'] = str(count) + " of " + str(len(arks_list))
        info['Bag-Group'] = os.path.split(path_to_objects)[1]
    bag = bagit.make_bag(bagname, bag_info=info, checksums=['md5','sha256'])
    if os.path.isdir(loc):
        shutil.copytree(loc, os.path.join(bagname, "data"), dirs_exist_ok=True)
    elif os.path.isfile(loc):
        destpath = os.path.join(bagname, "data", os.path.basename(loc))
        shutil.copyfile(loc, destpath)
    # Get FITS metadata
    os.mkdir(os.path.join(bagname, "data", "metadata"))
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






#--- To-do: descriptive metadata
# can I get the ERC metadata via api? E.g. "resolver/ark:/naan/uuid/?"

