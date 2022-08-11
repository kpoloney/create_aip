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
```

# Scripts

[aiptools](#aiptools) contains functions required for the other scripts. 

[mint_islandora_ARK](#mint_islandora_ark) creates an ARK identifier for Islandora objects.

[islandora_METS](#islandora_mets) creates METS files for Islandora objects. 

[local_objects](#local_objects) creates AIPs for objects stored locally that is not intended to be hosted online.

## aiptools

This script contains functions which are imported by the other scripts for retrieving Islandora metadata. 

## islandora_METS

This script creates METS files for Islandora objects. The script uses Islandora field models taxonomy and `memberOf`
information to convey parent-child relationships.

The script has two arguments: 
- `--config` points to the configuration YAML file.
- `--outputdir` Optional, specify an output directory the XML files will be written to. By default, the files will be 
  saved to the same folder as the script.

If no NAAN is given in the configuration file, the script will use the Islandora URL for the METS `FLocat` field. 

## local_objects

This script creates AIPs for objects that are stored locally and will not be hosted online. If the object does not
have an ARK already indexed in [larkm](https://github.com/mjordan/larkm), then one will be minted.

Users must have [FITS](https://projects.iq.harvard.edu/fits/get-started-using-fits) installed, must have access to
the drive location on which objects are saved, and have permission to query the larkm API.

## mint_islandora_ARK

This script automatically mints ARKs for Islandora objects. Islandora metadata is used to populate the ERC metadata
required for the ARK, and the Drupal UUID is used as the ARK identifier. The script uses 
[Larkm](https://github.com/mjordan/larkm) to mint ARKs. 

The script has three arguments:
- `--config` points to the configuration YAML file
- `--get_nodes` indicates whether the script should automatically get new node IDs from Islandora
- `--date` If `--get_nodes` is True, indicate the date to search for new nodes. Input date in YYYYMMDD format