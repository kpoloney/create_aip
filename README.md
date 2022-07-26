# Create AIPs

This repository contains scripts to automate the creation of archival information packages (AIPs) for SFU's digital
objects.

AIP and Bag structure are created according to the SFU [AIP Specification](https://github.com/kpoloney/aip_spec).

# Scripts

[Aiptools](#aiptools) contains functions required for the other scripts. 

[mint_islandora_ARK](#mint_islandora_ark) creates an ARK identifier for Islandora objects.

[islandora_METS](#islandora_mets) creates METS files for Islandora objects. 

[local_object](#local_object) creates AIPs for objects stored locally that is not intended to be hosted online.

## aiptools

Functions are imported by the other scripts. Contains automation for getting Islandora metadata. 

## islandora_METS

This script creates METS files for Islandora objects. The script uses Islandora field models taxonomy and `memberOf` 
information to convey parent-child relationships.

## local_object

This script creates AIPs for objects that are stored locally and will not be hosted online. If the object does not
have an ARK already indexed in larkm, then one will be minted.

Users must have [FITS](https://projects.iq.harvard.edu/fits/get-started-using-fits) installed, must have access to
the drive location on which objects are saved, and have permission to query the larkm API.

## mint_islandora_ARK

This script automatically mints ARKs for objects, using a text file or space-separated list of node IDs as input.
Islandora metadata is used to populate the ERC metadata required for the ARK.