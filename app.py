from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Update file path references from root directory to data folder
GVL_FILE_PATH = 'data/gvl.json'  # Updated path
VENDOR_DATA_FILE_PATH = 'data/vendor_data.json'  # Updated path

# Set this to True to enable updates without password
ENABLE_UPDATES_WITHOUT_PASSWORD = True

# Get the update password from environment variable
# If not set, updates will be disabled unless ENABLE_UPDATES_WITHOUT_PASSWORD is True
UPDATE_PASSWORD = os.environ.get('UPDATE_PASSWORD', None)

# Function to load vendor data from JSON file
def load_vendor_data():
    try:
        with open(VENDOR_DATA_FILE_PATH, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading vendor data: {e}")
        return {}

# Function to save vendor data to JSON file
def save_vendor_data(data):
    """Save updated vendor data to the JSON file"""
    try:
        with open(VENDOR_DATA_FILE_PATH, 'w') as file:
            json.dump(data, file, indent=4)
        return True
    except Exception as e:
        print(f"Error saving vendor data: {e}")
        return False

# Function to convert "C, LI" strings to arrays ["C", "LI"]
def convert_cli_to_arrays():
    vendor_data = load_vendor_data()
    updated = False
    
    if 'vendors' in vendor_data:
        for vendor_id, vendor_info in vendor_data['vendors'].items():
            # Check all purpose fields for "C, LI" values
            purpose_fields = [f'p{i}' for i in range(1, 11)] + [f'sp{i}' for i in range(1, 3)] + [f'f{i}' for i in range(1, 4)] + [f'sf{i}' for i in range(1, 3)]
            
            for field in purpose_fields:
                if field in vendor_info and vendor_info[field] == "C, LI":
                    vendor_info[field] = ["C", "LI"]
                    updated = True
    
    if updated:
        save_vendor_data(vendor_data)
        print("Updated 'C, LI' values to arrays in vendor_data.json")
    
    return vendor_data

# Function to ensure all vendors from GVL are in vendor_data.json with complete data structure
def ensure_all_vendors_in_data():
    # Load the GVL data
    try:
        with open(GVL_FILE_PATH, 'r') as f:
            gvl_data = json.load(f)
    except:
        # If file doesn't exist, fetch it from the IAB
        response = requests.get('https://vendor-list.consensu.org/v3/vendor-list.json')
        if response.status_code == 200:
            gvl_data = response.json()
            # Save the GVL data for future use
            with open(GVL_FILE_PATH, 'w') as f:
                json.dump(gvl_data, f, indent=2)
        else:
            print("Failed to fetch GVL data")
            return
    
    # Load current vendor data
    vendor_data = load_vendor_data()
    
    # Initialize vendors dict if it doesn't exist
    if 'vendors' not in vendor_data:
        vendor_data['vendors'] = {}
    
    # Ensure all vendors from GVL are in vendor_data.json
    for vendor_id, vendor_info in gvl_data['vendors'].items():
        if vendor_id not in vendor_data['vendors']:
            # Add the vendor with default values
            vendor_data['vendors'][vendor_id] = {
                'name': vendor_info['name'],
                'status': '',
                'mblAudited': 'No/Unknown',
                'vendorTypes': []
            }
            
            # Add purpose fields
            for i in range(1, 11):
                field = f'p{i}'
                if 'purposes' in vendor_info and i in vendor_info['purposes']:
                    vendor_data['vendors'][vendor_id][field] = "C"
                elif 'legIntPurposes' in vendor_info and i in vendor_info['legIntPurposes']:
                    vendor_data['vendors'][vendor_id][field] = "LI"
                elif 'flexiblePurposes' in vendor_info and i in vendor_info['flexiblePurposes']:
                    vendor_data['vendors'][vendor_id][field] = ["C", "LI"]
                else:
                    vendor_data['vendors'][vendor_id][field] = ""
            
            # Add special purpose fields
            for i in range(1, 3):
                field = f'sp{i}'
                if 'specialPurposes' in vendor_info and i in vendor_info['specialPurposes']:
                    vendor_data['vendors'][vendor_id][field] = "LI"
                else:
                    vendor_data['vendors'][vendor_id][field] = ""
            
            # Add feature fields
            for i in range(1, 4):
                field = f'f{i}'
                if 'features' in vendor_info and i in vendor_info['features']:
                    vendor_data['vendors'][vendor_id][field] = "LI"
                else:
                    vendor_data['vendors'][vendor_id][field] = ""
            
            # Add special feature fields
            for i in range(1, 3):
                field = f'sf{i}'
                if 'specialFeatures' in vendor_info and i in vendor_info['specialFeatures']:
                    vendor_data['vendors'][vendor_id][field] = "C"
                else:
                    vendor_data['vendors'][vendor_id][field] = ""
    
    # Save the updated data
    save_vendor_data(vendor_data)
    
    return vendor_data

# Function to process vendor data - shared between routes
def process_vendor_data():
    # Ensure all vendors are in vendor_data.json with complete data
    vendor_data = ensure_all_vendors_in_data()
    
    # Load the GVL data
    try:
        with open(GVL_FILE_PATH, 'r') as f:
            gvl_data = json.load(f)
    except:
        # If file doesn't exist, fetch it from the IAB
        response = requests.get('https://vendor-list.consensu.org/v3/vendor-list.json')
        gvl_data = response.json()
        with open(GVL_FILE_PATH, 'w') as f:
            json.dump(gvl_data, f)
    
    # Process vendor data
    vendors = []
    for vendor_id, vendor_info in gvl_data['vendors'].items():
        if vendor_id in vendor_data.get('vendors', {}):
            # Get the stored vendor data
            custom_data = vendor_data['vendors'][vendor_id]
            
            # Create a vendor object with data from vendor_data.json
            vendor = {
                'id': vendor_id,
                'name': custom_data.get('name', vendor_info['name']),
                'status': custom_data.get('status', ''),
                'mblAudited': custom_data.get('mblAudited', 'No/Unknown'),
                'vendorTypes': custom_data.get('vendorTypes', []),
                'p1': custom_data.get('p1', '-'), 
                'p2': custom_data.get('p2', '-'), 
                'p3': custom_data.get('p3', '-'), 
                'p4': custom_data.get('p4', '-'), 
                'p5': custom_data.get('p5', '-'),
                'p6': custom_data.get('p6', '-'), 
                'p7': custom_data.get('p7', '-'), 
                'p8': custom_data.get('p8', '-'), 
                'p9': custom_data.get('p9', '-'), 
                'p10': custom_data.get('p10', '-'),
                'sp1': custom_data.get('sp1', '-'), 
                'sp2': custom_data.get('sp2', '-'),
                'f1': custom_data.get('f1', '-'), 
                'f2': custom_data.get('f2', '-'), 
                'f3': custom_data.get('f3', '-'),
                'sf1': custom_data.get('sf1', '-'), 
                'sf2': custom_data.get('sf2', '-')
            }
            
            vendors.append(vendor)
    
    return vendors

@app.route('/')
@app.route('/home')
def index():
    # Ensure all vendors are in vendor_data.json when app starts
    ensure_all_vendors_in_data()
    return render_template('index.html')

@app.route('/vendor-management')
def vendor_management():
    # Use the same vendor data processing as vendorlist
    vendors = process_vendor_data()
    return render_template('vendor-management.html', vendors=vendors, update_enabled=True)

@app.route('/purposeslist')
def purposeslist():
    # Use the same vendor data processing as vendorlist
    vendors = process_vendor_data()
    return render_template('purposeslist.html', vendors=vendors, update_enabled=True)

@app.route('/vendorlist')
def vendorlist():
    # Load GVL data
    try:
        with open('data/gvl.json', 'r', encoding='utf-8') as f:
            gvl_data = json.load(f)
    except Exception as e:
        print(f"Error loading GVL data: {e}")
        gvl_data = {"vendors": {}}
    
    # Load custom vendor data
    try:
        with open('data/vendor_data.json', 'r', encoding='utf-8') as f:
            vendor_data = json.load(f)
    except Exception as e:
        print(f"Error loading vendor data: {e}")
        vendor_data = {}
    
    # Combine data
    vendors = []
    for vendor_id, vendor in gvl_data["vendors"].items():
        vendor_id = int(vendor_id)
        
        # Add custom data if available
        custom_data = vendor_data.get(str(vendor_id), {})
        
        # Create combined vendor object
        combined_vendor = {
            "id": vendor_id,
            "name": vendor.get("name", ""),
            "purposes": vendor.get("purposes", []),
            "legIntPurposes": vendor.get("legIntPurposes", []),
            "flexiblePurposes": vendor.get("flexiblePurposes", []),
            "specialPurposes": vendor.get("specialPurposes", []),
            "features": vendor.get("features", []),
            "specialFeatures": vendor.get("specialFeatures", []),
            "policyUrl": vendor.get("policyUrl", ""),
            "cookieMaxAgeSeconds": vendor.get("cookieMaxAgeSeconds", ""),
            "usesCookies": vendor.get("usesCookies", False),
            "usesNonCookieAccess": vendor.get("usesNonCookieAccess", False),
            "deviceStorageDisclosureUrl": vendor.get("deviceStorageDisclosureUrl", ""),
            # Custom data
            "status": custom_data.get("status", ""),
            "vendorTypes": custom_data.get("vendorTypes", []),
            "mblAudited": custom_data.get("mblAudited", "No/Unknown")
        }
        
        vendors.append(combined_vendor)
    
    # Sort vendors by ID
    vendors.sort(key=lambda x: x["id"])
    
    return render_template('vendorlist.html', vendors=vendors)

@app.route('/inspect-vendor', methods=['GET'])
def inspect_vendor():
    # Get vendor ID from query parameter
    vendor_id = request.args.get('vendor_id', '')
    
    # Load vendor data
    vendor_data = load_vendor_data()
    
    # Load GVL data
    try:
        with open(GVL_FILE_PATH, 'r') as f:
            gvl_data = json.load(f)
    except Exception as e:
        print(f"Error loading GVL data: {e}")
        gvl_data = {"vendors": {}}
    
    # Prepare list of all vendors for dropdown
    all_vendors = []
    for vendor_id_item, vendor_info in gvl_data['vendors'].items():
        all_vendors.append({
            'id': vendor_id_item,
            'name': vendor_info.get('name', f'Vendor {vendor_id_item}')
        })
    
    # Sort vendors by name
    all_vendors.sort(key=lambda x: x['name'].lower())
    
    # Initialize selected vendor
    selected_vendor = None
    raw_vendor_data = None
    
    # If vendor ID is provided, get its data
    if vendor_id:
        # Get vendor data from GVL
        gvl_vendor = gvl_data.get('vendors', {}).get(vendor_id, {})
        
        # Get custom vendor data
        custom_vendor = vendor_data.get('vendors', {}).get(vendor_id, {})
        
        # Store the raw vendor data from GVL
        if gvl_vendor:
            raw_vendor_data = gvl_vendor
            
            # Combine data
            selected_vendor = {
                'id': vendor_id,
                'name': gvl_vendor.get('name', ''),
                'policyUrl': gvl_vendor.get('policyUrl', ''),
                'purposes': gvl_vendor.get('purposes', {}),
                'legIntPurposes': gvl_vendor.get('legIntPurposes', {}),
                'specialPurposes': gvl_vendor.get('specialPurposes', {}),
                'features': gvl_vendor.get('features', {}),
                'specialFeatures': gvl_vendor.get('specialFeatures', {}),
                'status': custom_vendor.get('status', ''),
                'mblAudited': custom_vendor.get('mblAudited', 'No/Unknown'),
                'vendorTypes': custom_vendor.get('vendorTypes', []),
                'cookieMaxAgeSeconds': gvl_vendor.get('cookieMaxAgeSeconds', ''),
                'usesCookies': gvl_vendor.get('usesCookies', ''),
                'usesNonCookieAccess': gvl_vendor.get('usesNonCookieAccess', ''),
                'deviceStorageDisclosureUrl': gvl_vendor.get('deviceStorageDisclosureUrl', ''),
                'deletedDate': gvl_vendor.get('deletedDate', ''),
                'overflow': gvl_vendor.get('overflow', {})
            }
            
            # Add custom purpose data
            purpose_fields = [f'p{i}' for i in range(1, 11)] + [f'sp{i}' for i in range(1, 3)] + [f'f{i}' for i in range(1, 4)] + [f'sf{i}' for i in range(1, 3)]
            for field in purpose_fields:
                if field in custom_vendor:
                    selected_vendor[field] = custom_vendor[field]
    
    return render_template('inspect-vendor.html', 
                          all_vendors=all_vendors, 
                          selected_vendor=selected_vendor,
                          raw_vendor_data=raw_vendor_data,
                          vendor_id=vendor_id)

@app.route('/update_vendor', methods=['POST'])
def update_vendor():
    try:
        data = request.json
        vendor_id = data.get('vendorId')
        field = data.get('field')
        value = data.get('value')
        password = data.get('password')
        
        # Debug: Print the update request
        print(f"Update request: Vendor {vendor_id}, Field {field}, Value {value}")
        
        # Check if updates are enabled
        if not UPDATE_PASSWORD and not ENABLE_UPDATES_WITHOUT_PASSWORD:
            return jsonify({'success': False, 'error': 'Updates are disabled'})
        
        # Check password if required
        if UPDATE_PASSWORD and not ENABLE_UPDATES_WITHOUT_PASSWORD and password != UPDATE_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid password'})
        
        if not vendor_id or not field:
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Load current vendor data
        vendor_data = load_vendor_data()
        
        # Initialize vendors dict if it doesn't exist
        if 'vendors' not in vendor_data:
            vendor_data['vendors'] = {}
        
        # Initialize vendor entry if it doesn't exist
        if vendor_id not in vendor_data['vendors']:
            # Load the GVL data to get the vendor name
            try:
                with open(GVL_FILE_PATH, 'r') as f:
                    gvl_data = json.load(f)
                    vendor_name = gvl_data['vendors'][vendor_id]['name']
            except:
                vendor_name = f"Vendor {vendor_id}"
            
            vendor_data['vendors'][vendor_id] = {
                'name': vendor_name,
                'status': '',
                'mblAudited': 'No/Unknown',
                'vendorTypes': []
            }
        
        # Update the field
        vendor_data['vendors'][vendor_id][field] = value
        
        # Debug: Print the updated vendor data
        print(f"Updated vendor data for {vendor_id}: {vendor_data['vendors'][vendor_id]}")
        
        # Save the updated data
        if save_vendor_data(vendor_data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save vendor data'})
    
    except Exception as e:
        print(f"Error in update_vendor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/compare-vendors', methods=['GET'])
def compare_vendors():
    # Get vendor IDs from query parameters
    vendor_id1 = request.args.get('vendor_id1', '')
    vendor_id2 = request.args.get('vendor_id2', '')
    
    # Load vendor data
    vendor_data = load_vendor_data()
    
    # Load GVL data
    try:
        with open(GVL_FILE_PATH, 'r') as f:
            gvl_data = json.load(f)
    except Exception as e:
        print(f"Error loading GVL data: {e}")
        gvl_data = {"vendors": {}}
    
    # Prepare list of all vendors for dropdowns
    all_vendors = []
    for vendor_id, vendor_info in gvl_data['vendors'].items():
        all_vendors.append({
            'id': vendor_id,
            'name': vendor_info.get('name', f'Vendor {vendor_id}')
        })
    
    # Sort vendors by name
    all_vendors.sort(key=lambda x: x['name'].lower())
    
    # Initialize selected vendors
    selected_vendor1 = None
    selected_vendor2 = None
    
    # If vendor IDs are provided, get their data
    if vendor_id1:
        selected_vendor1 = get_vendor_details(vendor_id1, gvl_data, vendor_data)
    
    if vendor_id2:
        selected_vendor2 = get_vendor_details(vendor_id2, gvl_data, vendor_data)
    
    return render_template('compare-vendors.html', 
                          all_vendors=all_vendors, 
                          selected_vendor1=selected_vendor1,
                          selected_vendor2=selected_vendor2,
                          vendor_id1=vendor_id1,
                          vendor_id2=vendor_id2)

# Helper function to get vendor details (reuse this for both inspect-vendor and compare-vendors)
def get_vendor_details(vendor_id, gvl_data, vendor_data):
    if not vendor_id:
        return None
        
    # Get vendor data from GVL
    gvl_vendor = gvl_data.get('vendors', {}).get(vendor_id, {})
    
    # Get custom vendor data
    custom_vendor = vendor_data.get('vendors', {}).get(vendor_id, {})
    
    # Combine data
    if gvl_vendor:
        selected_vendor = {
            'id': vendor_id,
            'name': gvl_vendor.get('name', ''),
            'policyUrl': gvl_vendor.get('policyUrl', ''),
            'purposes': gvl_vendor.get('purposes', {}),
            'legIntPurposes': gvl_vendor.get('legIntPurposes', {}),
            'specialPurposes': gvl_vendor.get('specialPurposes', {}),
            'features': gvl_vendor.get('features', {}),
            'specialFeatures': gvl_vendor.get('specialFeatures', {}),
            'status': custom_vendor.get('status', ''),
            'mblAudited': custom_vendor.get('mblAudited', 'No/Unknown'),
            'vendorTypes': custom_vendor.get('vendorTypes', []),
            'cookieMaxAgeSeconds': gvl_vendor.get('cookieMaxAgeSeconds', ''),
            'usesCookies': gvl_vendor.get('usesCookies', ''),
            'usesNonCookieAccess': gvl_vendor.get('usesNonCookieAccess', ''),
            'deviceStorageDisclosureUrl': gvl_vendor.get('deviceStorageDisclosureUrl', ''),
            'deletedDate': gvl_vendor.get('deletedDate', ''),
            'overflow': gvl_vendor.get('overflow', {})
        }
        
        # Add custom purpose data
        purpose_fields = [f'p{i}' for i in range(1, 11)] + [f'sp{i}' for i in range(1, 3)] + [f'f{i}' for i in range(1, 4)] + [f'sf{i}' for i in range(1, 3)]
        for field in purpose_fields:
            if field in custom_vendor:
                selected_vendor[field] = custom_vendor[field]
        
        return selected_vendor
    
    return None

if __name__ == '__main__':
    # Ensure all vendors are in vendor_data.json when app starts
    ensure_all_vendors_in_data()
    # Convert "C, LI" strings to arrays
    convert_cli_to_arrays()
    app.run(debug=True)