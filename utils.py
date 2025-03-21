import json

# Update file path references
GVL_FILE_PATH = 'data/gvl.json'  # Updated path
VENDOR_DATA_FILE_PATH = 'data/vendor_data.json'  # Updated path

def read_gvl_file():
    """Read and parse the GVL JSON file"""
    with open(GVL_FILE_PATH, 'r') as file:
        return json.load(file)

def read_vendor_data_file():
    """Read and parse the vendor data JSON file"""
    with open(VENDOR_DATA_FILE_PATH, 'r') as file:
        return json.load(file) 