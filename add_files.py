import argparse
import os
import shutil
import bagit
import aiptools

parser = argparse.ArgumentParser()
parser.add_argument('--files_to_add', required=True,
                    help="Path to file(s) to add to bag. For multiple files, enter filenames as a comma-separated list.")
parser.add_argument('--bag_loc', required=True, help='Path to bag')
args = parser.parse_args()
if os.path.exists(args.bag_loc):
    bag_loc = args.bag_loc
else:
    raise SystemExit(args.bag_loc + " path does not exist")
files = []
if len(args.files_to_add.split(','))>1:
    for item in args.files_to_add.split(','):
        files.append(item.strip())
else:
    files.append(args.files_to_add)
for file in files:
    shutil.copy(file, os.path.join(bag_loc, "data"))
bag = bagit.Bag(bag_loc)
bagsize = aiptools.bagsize_units(aiptools.get_bag_size(os.path.join(bag_loc, "data")))
bag.info['Bag-Size'] = bagsize
bag.save(manifests=True)