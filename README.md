# Create AIPs

This repository contains scripts to automate the creation of archival information packages (AIPs) for SFU's digital
objects.

AIP and Bag structure are created according to the SFU [AIP Specification](https://github.com/kpoloney/aip_spec).

# Configuration

Information about the repository and the node IDs to be processed is contained in a YAML configuration file.

```yaml

# Base URL of islandora repository
repo_url: 'https://example-repo.com'

# User authentication to use the REST API for Islandora
auth: ['user', 'pw']

# Either a list of node IDs or the location of a text file containing space-separated node IDs.
node_ids: [12345, 6789, 101112]

# Base URL of larkm host
larkm_host: 'http://example.com/larkm/'

# If using ARKs, enter the institutional NAAN
ark_naan: '99999'

# Indicate ARK shoulder for objects.
ark_shoulder: 's1'

# Specify directory to save METS XML files. Otherwise, they will be saved in the same folder as the script. 
mets_dir: '/metadata/METS'

```

# Scripts

Scripts are organized based on which workflow is being followed. For objects that are stored locally (whether with 
additional metadata on AtoM or not), use scripts in the [Local](/Local) directory. For objects that are stored on 
Islandora, use the scripts in the [Islandora](/Islandora) directory. The AIP tools functions are used regardless of 
workflow. The validation script can be used at any time after an AIP bag is created for either workflow.

[aiptools](#aiptools) contains functions required for the other scripts. 

[validate_aip](#validate-aip) validates a completed AIP against the AIP specification and BagIt specification. 

[add_files](#add-files) adds any additional files to a Bag and updates the manifests and bag-info file.

## aiptools

This script contains functions which are imported by the other scripts for retrieving Islandora metadata. 

## Validate AIP

This script is to be run to validate a completed AIP. It checks for required ERC metadata and conformity to the 
BagIt Profile and BagIt specification. 

The script has four arguments:
- `--bag_dir` is the directory of bags to be validated
- `--profile_url` is the ARK or URL of the BagIt profile
- `--larkm_url` (optional) the base URL of larkm. It is only required if the BagIt profile URI is an ARK indexed in 
  larkm.
- `--clamav` (optional) the file location of the virus scan software ClamAV. 

## Add files

This script is for adding files to an AIP after it has already been Bagged. If files need to be added later to a 
Bag, use this script to include them in the `data` directory and update the Bag's manifests.

The script has two arguments:
- `--files_to_add` is a filepath or comma-separated list of multiple files to be added to the bag.
- `--bag_loc` is the filepath to the bag.

# Local workflow scripts

These scripts should be completed in the following order, as some scripts depend on the output of others.

1. [get_atom_metadata](#get-atom-descriptions) (optional) If there is additional metadata from AtoM to be added, this 
   script will use the REST API to download the object's description and create an ERC metadata file from it. 
2. [mint_local_ARK](#mint-ark-for-local-objects) creates an ARK identifier for objects stored locally.
   1. Objects must have an ARK before the AIP bag is created. 
3. [local_objects](#local-objects) creates bagged AIPs for objects that are not intended to be hosted online.

See the [Local Workflow Steps](https://github.com/kpoloney/aip_spec/blob/main/local_workflow.md) for more information.

## Get AtoM Descriptions

This script uses the AtoM REST API to request description information for the object. The REST API plugin must be 
enabled in AtoM. A valid AtoM login and object slug are also required. The ERC metadata file to be used in minting 
the ARK will be created from the AtoM description.

The script takes three arguments:
- `--atom_url` is the base URL for AtoM
- `--slug` is the [AtoM slug](https://www.accesstomemory.org/en/docs/2.6/user-manual/glossary/glossary/#term-slug) for the object.
- `--obj_dir` is the path to the parent directory of the object.

## Mint ARK for local objects

This script creates ARKs for objects stored locally. The script takes three arguments:
- `--larkm` requires the base url of the larkm host.
- `--objects` is the location of either a single file or folder to be processed or a directory of objects to process.
- `--single_obj` if minting an ARK for only one object, set this argument to "True" if the `--objects` argument is not 
  a single file. Otherwise, all items within the directory will each be given an ARK.

Refer to the [Local workflow Document](https://github.com/kpoloney/aip_spec/blob/main/local_workflow.md) to ensure 
the ERC metadata is included correctly. If the script cannot locate or parse the minimum metadata, the ARK will not 
be minted.

## Local Objects

This script creates AIPs for objects that are stored locally and will not be hosted online. If the object does not
have an ARK already indexed in [larkm](https://github.com/mjordan/larkm), then you will have to first run the 
`mint_local_ARK.py` script.

Users must have [FITS](https://projects.iq.harvard.edu/fits/get-started-using-fits) installed if technical metadata will
be included. Users must have access to the drive location on which objects are saved, and have permission to query the
larkm API.

The script has four arguments:
- `--objects` is the location of the directory of objects to be processed.
- `--output_dir` is the directory to which bags will be saved
- `--larkm` the base url of the larkm host
- `--fits` optional; the location of the FITS tool if including technical metadata.

# Islandora workflow scripts

These scripts should be completed in the following order, as some may depend on the output of others.

1. [mint_islandora_ARK](#mint-islandora-ark) creates an ARK identifier for Islandora objects.
   1. An ARK is required for the creation of an AIP bag.
2. [islandora_METS](#create-mets) (optional) creates METS files for Islandora objects. 
3. [make_bag_islandora](#make-islandora-bag) completes and Bags the AIP for Islandora objects using Islandora Bagger.

## Mint Islandora ARK

This script automatically mints ARKs for Islandora objects. Islandora metadata is used to populate the ERC metadata
required for the ARK, and the Drupal UUID is used as the ARK identifier. The script uses 
[Larkm](https://github.com/mjordan/larkm) to mint ARKs. 

The script has three arguments:
- `--config` points to the configuration YAML file
- `--get_nodes` indicates whether the script should automatically get new node IDs from Islandora
- `--date` If `--get_nodes` is True, indicate the date to search for new nodes. Input date in YYYYMMDD format

## Create METS

This script creates METS files for Islandora objects. The script uses Islandora field models taxonomy and `memberOf`
information to convey parent-child relationships.

The script has one argument: 
- `--config` points to the configuration YAML file.

If no NAAN is given in the configuration file, the script will use the Islandora URL for the METS `FLocat` field.

## Make Islandora bag

This script is the final step of AIP creation for Islandora objects. It uses Islandora Bagger to create bags for 
each node ID in the configuration file. METS files are added using the Islandora Bagger plugin `AddFile`.

The script has two arguments:
- `--config` points to the AIP configuration YAML file
- `--bagger_config` points to the configuration YAML file for Islandora Bagger. If not specified, the script will 
  create one.