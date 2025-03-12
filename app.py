from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Path to the vendor data JSON file
VENDOR_DATA_FILE = os.path.join(os.path.dirname(__file__), 'vendor_data.json')

# Set this to True to enable updates without password
ENABLE_UPDATES_WITHOUT_PASSWORD = True

# Get the update password from environment variable
# If not set, updates will be disabled unless ENABLE_UPDATES_WITHOUT_PASSWORD is True
UPDATE_PASSWORD = os.environ.get('UPDATE_PASSWORD', None)

# Function to load vendor data from JSON file
def load_vendor_data():
    if os.path.exists(VENDOR_DATA_FILE):
        try:
            with open(VENDOR_DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading vendor data: {e}")
            return {"vendors": {}}
    return {"vendors": {}}

# Function to save vendor data to JSON file
def save_vendor_data(data):
    try:
        with open(VENDOR_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving vendor data: {e}")
        return False

# Function to ensure all vendors from GVL are in vendor_data.json with complete data structure
def ensure_all_vendors_in_data():
    # Load the GVL data
    try:
        with open('gvl.json', 'r') as f:
            gvl_data = json.load(f)
    except:
        # If file doesn't exist, fetch it from the IAB
        response = requests.get('https://vendor-list.consensu.org/v3/vendor-list.json')
        gvl_data = response.json()
        with open('gvl.json', 'w') as f:
            json.dump(gvl_data, f)
    
    # Load current vendor data
    vendor_data = load_vendor_data()
    
    # Ensure vendors dict exists
    if 'vendors' not in vendor_data:
        vendor_data['vendors'] = {}
    
    # Add entries for all vendors in GVL with complete data structure
    updated = False
    for vendor_id, vendor_info in gvl_data['vendors'].items():
        # Process purposes according to the new rules
        purpose_values = {}
        
        # Process regular purposes (P1-P10)
        for i in range(1, 11):
            purpose_str = str(i)
            
            # Check if in flexiblePurposes
            if 'flexiblePurposes' in vendor_info and purpose_str in map(str, vendor_info['flexiblePurposes']):
                purpose_values[f'p{i}'] = "C, LI"
            # Check if in legIntPurposes
            elif 'legIntPurposes' in vendor_info and purpose_str in map(str, vendor_info['legIntPurposes']):
                purpose_values[f'p{i}'] = "LI"
            # Check if in purposes
            elif 'purposes' in vendor_info and purpose_str in map(str, vendor_info['purposes']):
                purpose_values[f'p{i}'] = "C"
            else:
                purpose_values[f'p{i}'] = "-"
        
        # Process special purposes (SP1-SP2)
        for i in range(1, 3):
            purpose_str = str(i)
            
            # Check if in specialPurposes
            if 'specialPurposes' in vendor_info and purpose_str in map(str, vendor_info['specialPurposes']):
                purpose_values[f'sp{i}'] = "LI"
            else:
                purpose_values[f'sp{i}'] = "-"
        
        # Process features (F1-F3)
        for i in range(1, 4):
            feature_str = str(i)
            
            # Check if in features
            if 'features' in vendor_info and feature_str in map(str, vendor_info['features']):
                purpose_values[f'f{i}'] = "LI"
            else:
                purpose_values[f'f{i}'] = "-"
        
        # Process special features (SF1-SF2)
        for i in range(1, 3):
            feature_str = str(i)
            
            # Check if in specialFeatures
            if 'specialFeatures' in vendor_info and feature_str in map(str, vendor_info['specialFeatures']):
                purpose_values[f'sf{i}'] = "C"
            else:
                purpose_values[f'sf{i}'] = "-"
        
        # Create default structure for this vendor
        default_vendor_data = {
            'name': vendor_info['name'],
            'status': '',
            'mblAudited': 'No/Unknown',
            'vendorTypes': [],
            **purpose_values  # Add all the purpose values
        }
        
        if vendor_id not in vendor_data['vendors']:
            # If vendor doesn't exist in our data, add it with default values
            vendor_data['vendors'][vendor_id] = default_vendor_data
            updated = True
        else:
            # If vendor exists, ensure all fields are present
            existing_vendor = vendor_data['vendors'][vendor_id]
            
            # Always update the name from GVL
            if existing_vendor.get('name') != vendor_info['name']:
                existing_vendor['name'] = vendor_info['name']
                updated = True
            
            # Update purpose values
            for key, value in purpose_values.items():
                existing_vendor[key] = value
                updated = True
            
            # Ensure all fields exist
            for key, value in default_vendor_data.items():
                if key not in existing_vendor:
                    existing_vendor[key] = value
                    updated = True
    
    # Save if changes were made
    if updated:
        save_vendor_data(vendor_data)
    
    return vendor_data

# Function to process vendor data - shared between routes
def process_vendor_data():
    # Ensure all vendors are in vendor_data.json with complete data
    vendor_data = ensure_all_vendors_in_data()
    
    # Load the GVL data
    try:
        with open('gvl.json', 'r') as f:
            gvl_data = json.load(f)
    except:
        # If file doesn't exist, fetch it from the IAB
        response = requests.get('https://vendor-list.consensu.org/v3/vendor-list.json')
        gvl_data = response.json()
        with open('gvl.json', 'w') as f:
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
def vendor_list():
    vendors = process_vendor_data()
    return render_template('vendorlist.html', vendors=vendors, update_enabled=True)

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
                with open('gvl.json', 'r') as f:
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

if __name__ == '__main__':
    # Ensure all vendors are in vendor_data.json when app starts
    ensure_all_vendors_in_data()
    app.run(debug=True)