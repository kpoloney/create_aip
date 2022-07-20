# Build an AIP from files

This script automates the creation of archival information packages (AIPs) for digital objects that are stored locally and are not intended to be hosted on the web. The objects' metadata, storage location, and ARK identifier should be indexed in [larkm](https://github.com/mjordan/larkm).

AIP and Bag structure are created according to the SFU [AIP Specification](https://github.com/kpoloney/aip_spec).


# Usage

Users must have [FITS](https://projects.iq.harvard.edu/fits/get-started-using-fits) installed. 

Users must have access to the drive location on which objects are saved and have permission to query the larkm API.