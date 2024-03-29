import logging
import requests
import argparse
import os
import sys
sys.path.append(os.path.dirname(os.path.getcwd()))
import aiptools
import yaml
from lxml import etree, isoschematron
import xml.etree.ElementTree as ET

logging.basicConfig(filename="create_aip.log", level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help='The location of the configuration YAML file.')
args = parser.parse_args()

# Load configuration file
try:
    with open(args.config, 'r') as y:
        config = yaml.safe_load(y)
except:
    logging.error("Could not open config file: " + args.config)
    raise SystemExit

repo_url = config['repo_url'].rstrip("/")
naan = config['ark_naan']
shoulder = config['ark_shoulder']
user = config['auth'][0]
pw = config['auth'][1]
outputdir = config['mets_dir']

# Register namespaces
ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
ET.register_namespace('mets', "http://www.loc.gov/METS/")
xlink="{http://www.w3.org/1999/xlink}"
mets="{http://www.loc.gov/METS/}"

# If NAAN left blank, use URL instead of ARKs for Flocat
if naan == "":
    id_type = "URL"
else:
    id_type = "ARK"

# List of node ids (function checks if nodes are a list or text file and returns a list of nids).
node_ids = aiptools.read_config_nodes(config)

for nid in node_ids:
    # Create main sections and root
    try:
        node = aiptools.get_node_json(repo_url, nid)
    except:
        logging.error("Could not retrieve node.json for " + str(nid))
        continue
    root = ET.Element(mets + 'mets', attrib={'LABEL':node['title'][0]['value']})
    filesec = ET.SubElement(root, mets + "fileSec")
    structmap = ET.SubElement(root, mets + "structMap", attrib={"TYPE": "logical"})
    main_level = ET.SubElement(structmap, mets + "div")
    # get main metadata for each nid
    try:
        members = aiptools.get_members(repo_url, nid, user, pw)
    except:
        logging.error("Could not retrieve members.json for " + str(nid))
        continue
    node_uuid = "uuid_" + node['uuid'][0]['value']
    if id_type == 'ARK':
        node_loc = "ark:" + naan + "/" + shoulder + node['uuid'][0]['value']
    else:
        node_loc = repo_url + "/node/" + str(nid)
    # Use external URI for field_model for fileGrp/type. Need secondary lookup for taxonomy json.
    model_url = repo_url + node['field_model'][0]['url'] + "?_format=json"
    try:
        node_model = aiptools.get_field_model(model_url)
    except:
        logging.error("Could not retrieve field model for: " + str(nid) + ". Enter fileGrp USE manually.")
        node_model = "ENTER FIELD MODEL"
    # Build node element tree
    node_grp = ET.SubElement(filesec, mets + "fileGrp", attrib={"USE": node_model})
    node_file = ET.SubElement(node_grp, mets + "file", attrib={"ID": node_uuid})
    node_flocat = ET.SubElement(node_file, mets + "FLocat", attrib={xlink + "href": node_loc, "LOCTYPE": id_type})
    node_fptr = ET.SubElement(main_level, mets + "fptr", attrib={"FILEID": node_uuid})
    # Keep dictionary of file groups to avoid repeated top-level sections
    grp = {node_model: node_grp}
    if len(members)>0: # members will be length 0 if there are no child objects
        child_level = ET.SubElement(main_level, mets+"div", attrib={"TYPE":"http://purl.org/dc/terms/hasPart"})
        # members will come out as a list of dictionaries if there are multiple children. Otherwise it is a dictionary.
        if len(members)>1:
            for i in range(len(members)):
                child_uuid = members[i]['uuid'][0]['value']
                fptr = ET.SubElement(child_level, mets+"fptr", attrib={"FILEID":"uuid_"+child_uuid})
                if id_type == 'ARK':
                    child_loc = "ark:"+ naan + "/" + shoulder + child_uuid
                else:
                    child_loc = repo_url+'/node/'+ str(members[i]['nid'][0]['value'])
                # get ext url for model
                c_url = repo_url + members[i]['field_model'][0]['url'] + "?_format=json"
                fgrp_type = aiptools.get_field_model(c_url)
                if fgrp_type not in grp.keys():
                    fgrp = ET.SubElement(filesec, mets+'fileGrp', attrib={"USE":fgrp_type})
                    file = ET.SubElement(fgrp, mets+"file", attrib={"ID":"uuid_"+child_uuid})
                    flocat = ET.SubElement(file, mets+"FLocat", attrib={xlink+"href":child_loc, "LOCTYPE":id_type})
                    grp[fgrp_type] = fgrp
                else:
                    parent = grp[fgrp_type]
                    file = ET.SubElement(parent, mets+"file", attrib={"ID":"uuid_"+child_uuid})
                    flocat = ET.SubElement(file, mets+'FLocat', attrib={xlink+"href":child_loc, "LOCTYPE":id_type})
        else:  # If there is only one child
            child_uuid = members['uuid'][0]['value']
            fptr = ET.SubElement(child_level, mets + "fptr", attrib={"FILEID": "uuid_" + child_uuid})
            if id_type == "ARK":
                child_loc = "ark:" + naan + "/" + shoulder + child_uuid
            else:
                child_loc = repo_url + '/node/' + str(members['nid'][0]['value'])
            c_url = repo_url + members['field_model'][0]['url'] + "?_format=json"
            try:
                fgrp_type = aiptools.get_field_model(c_url)
            except:
                logging.error("Could not retrieve field model for:" + str(members['nid'][0]['value']) + ". Enter fileGrp USE attribute manually.")
                fgrp_type = "ENTER FILE GROUP TYPE"
            if fgrp_type not in grp.keys():
                fgrp = ET.SubElement(filesec, mets + 'fileGrp', attrib={"USE": fgrp_type})
                file = ET.SubElement(fgrp, mets + "file", attrib={"ID": "uuid_" + child_uuid})
                flocat = ET.SubElement(file, mets + "FLocat", attrib={xlink + "href": child_loc, "LOCTYPE": id_type})
                grp[fgrp_type] = fgrp
            else:
                parent = grp[fgrp_type]
                file = ET.SubElement(parent, mets + "file", attrib={"ID": "uuid_"+child_uuid})
                flocat = ET.SubElement(file, mets + 'FLocat', attrib={xlink + "href": child_loc, "LOCTYPE": id_type})
    if len(node['field_member_of'])>0:
        parent_level = ET.SubElement(main_level, mets+"div", attrib={"TYPE":"http://purl.org/dc/terms/isPartOf"})
        # if there are multiple parents:
        if len(node['field_member_of'])>1:
            p_url = []
            for i in range(len(node['field_member_of'])):
                url = repo_url + node['field_member_of'][i]['url']+'?_format=json'
                p_url.append(url)
            for j in range(len(p_url)):
                #get node.json for parent objects
                r = requests.get(p_url[j])
                if r.status_code == 200:
                    parent_node = r.json()
                    uuid = parent_node['uuid'][0]['value']
                    fptr = ET.SubElement(parent_level, mets+"fptr", attrib={"FILEID":"uuid_"+uuid})
                    if id_type == 'ARK':
                        parent_loc = "ark:" + naan + "/" + shoulder + uuid
                    else:
                        parent_loc = repo_url + "/node/" + str(parent_node['nid'][0]['value'])
                    # Get parent model type for file grp from taxonomy json
                    model_url = repo_url + parent_node['field_model'][0]['url'] + "?_format=json"
                    model = aiptools.get_field_model(model_url)
                    if model not in grp.keys():
                        pgrp = ET.SubElement(filesec, mets + 'fileGrp', attrib={"USE": model})
                        pfile = ET.SubElement(pgrp, mets+'file', attrib={'ID':"uuid_"+uuid})
                        pflocat = ET.SubElement(pfile, mets+'FLocat', attrib={xlink+"href":parent_loc, "LOCTYPE":id_type})
                        grp[model]=pgrp
                    else:
                        filegroup = grp[model]
                        pfile = ET.SubElement(filegroup, mets+"file", attrib={'ID':"uuid_"+uuid})
                        pflocat = ET.SubElement(pfile, mets+"FLocat", attrib={xlink+"href":parent_loc, "LOCTYPE":id_type})
                else:
                    logging.error("Could not get node.json for parent node: " + str(p_url[j]))
        else:
            p_url = repo_url + node['field_member_of'][0]['url'] + "?_format=json"
            r = requests.get(p_url)
            if r.status_code == 200:
                parent_node = r.json()
                uuid = parent_node['uuid'][0]['value']
                fptr = ET.SubElement(parent_level, mets+"fptr", attrib={"FILEID":"uuid_"+uuid})
                if id_type == 'ARK':
                    parent_loc = "ark:"+ naan + "/" + shoulder + uuid
                else:
                    parent_loc = repo_url+'/node/'+str(parent_node['nid'][0]['value'])
                # Get parent model type for file grp from taxonomy json
                model_url = repo_url + parent_node['field_model'][0]['url'] + "?_format=json"
                model = aiptools.get_field_model(model_url)
                if model not in grp.keys():
                    pgrp = ET.SubElement(filesec, mets + 'fileGrp', attrib={"USE": model})
                    pfile = ET.SubElement(pgrp, mets + 'file', attrib={'ID': "uuid_" + uuid})
                    pflocat = ET.SubElement(pfile, mets + 'FLocat', attrib={xlink + "href": parent_loc, "LOCTYPE": id_type})
                    grp[model] = pgrp
                else:
                    filegroup = grp[model]
                    pfile = ET.SubElement(filegroup, mets + "file", attrib={'ID': "uuid_" + uuid})
                    pflocat = ET.SubElement(pfile, mets + "FLocat", attrib={xlink + "href": parent_loc, "LOCTYPE": id_type})
            else:
                logging.error("Could not get node.json for parent node: " + str(p_url))
    tree = ET.ElementTree(root)
    ET.indent(tree, space='\t')
    if outputdir is not None and os.path.exists(outputdir):
        filename = os.path.join(outputdir, str(nid) +"_mets.xml")
    else:
        filename = str(nid) + "_mets.xml"
    tree.write(filename, xml_declaration=False, encoding='utf-8')