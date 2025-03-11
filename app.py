from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Path to the vendor data JSON file
VENDOR_DATA_FILE = os.path.join(os.path.dirname(__file__), 'vendor_data.json')

# Get the update password from environment variable
# If not set, updates will be disabled
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vendorlist')
def vendor_list():
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
    
    # Load custom vendor data
    vendor_data = load_vendor_data()
    
    # Process vendor data
    vendors = []
    for vendor_id, vendor_info in gvl_data['vendors'].items():
        # Create a vendor object with default values
        vendor = {
            'id': vendor_id,
            'name': vendor_info['name'],
            'status': '',
            'mblAudited': 'No/Unknown',  # Default value for MBL Audited
            'vendorTypes': [],
            'p1': 0, 'p2': 0, 'p3': 0, 'p4': 0, 'p5': 0,
            'p6': 0, 'p7': 0, 'p8': 0, 'p9': 0, 'p10': 0,
            'sp1': 0, 'sp2': 0,
            'f1': 0, 'f2': 0, 'f3': 0,
            'sf1': 0, 'sf2': 0
        }
        
        # Update with custom data if available
        if vendor_id in vendor_data.get('vendors', {}):
            custom_data = vendor_data['vendors'][vendor_id]
            if 'status' in custom_data:
                vendor['status'] = custom_data['status']
            if 'mblAudited' in custom_data:
                vendor['mblAudited'] = custom_data['mblAudited']
            if 'vendorTypes' in custom_data:
                vendor['vendorTypes'] = custom_data['vendorTypes']
        
        # Add purposes data from GVL
        if 'purposes' in vendor_info:
            for purpose_id in vendor_info['purposes']:
                if 1 <= purpose_id <= 10:
                    vendor[f'p{purpose_id}'] = 1  # Consent
        
        if 'legIntPurposes' in vendor_info:
            for purpose_id in vendor_info['legIntPurposes']:
                if 1 <= purpose_id <= 10:
                    if vendor[f'p{purpose_id}'] == 1:
                        vendor[f'p{purpose_id}'] = 3  # Both C and LI
                    else:
                        vendor[f'p{purpose_id}'] = 2  # LI only
        
        # Add special purposes
        if 'specialPurposes' in vendor_info:
            for sp_id in vendor_info['specialPurposes']:
                if 1 <= sp_id <= 2:
                    vendor[f'sp{sp_id}'] = 1
        
        # Add features
        if 'features' in vendor_info:
            for f_id in vendor_info['features']:
                if 1 <= f_id <= 3:
                    vendor[f'f{f_id}'] = 1
        
        # Add special features
        if 'specialFeatures' in vendor_info:
            for sf_id in vendor_info['specialFeatures']:
                if 1 <= sf_id <= 2:
                    vendor[f'sf{sf_id}'] = 1
        
        vendors.append(vendor)
    
    # Sort vendors by name
    vendors.sort(key=lambda x: x['name'].lower())
    
    # Debug: Print the first few vendors to check if mblAudited is loaded correctly
    for i in range(min(3, len(vendors))):
        print(f"Vendor {vendors[i]['id']}: {vendors[i]['name']} - MBL Audited: {vendors[i]['mblAudited']}")
        print(f"Vendor Types: {vendors[i]['vendorTypes']}")
    
    return render_template('vendorlist.html', vendors=vendors, update_enabled=UPDATE_PASSWORD is not None)

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
        
        # Check if updates are enabled and password matches
        if not UPDATE_PASSWORD:
            return jsonify({'success': False, 'error': 'Updates are disabled'})
        
        if password != UPDATE_PASSWORD:
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
            vendor_data['vendors'][vendor_id] = {}
        
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

@app.route('/vendorlist')
def vendorlist():
    try:
        # Fetch the real vendor list from the IAB TCF API
        response = requests.get('https://vendor-list.consensu.org/v2/vendor-list.json')
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        # Load saved vendor data
        vendor_data = load_vendor_data()
        
        # Extract purposes data
        purposes_data = []
        for purpose_id, purpose_info in data.get('purposes', {}).items():
            # Determine what the framework allows for this purpose
            # This is example data - you would need to replace with actual framework rules
            framework_allows = {
                "1": {"C": True, "LI": False},  # Purpose 1: Only Consent
                "2": {"C": True, "LI": True},   # Purpose 2: Both Consent and LI
                "3": {"C": True, "LI": True},   # Purpose 3: Both Consent and LI
                "4": {"C": True, "LI": True},   # Purpose 4: Both Consent and LI
                "5": {"C": True, "LI": False},  # Purpose 5: Only Consent
                "6": {"C": True, "LI": False},  # Purpose 6: Only Consent
                "7": {"C": True, "LI": True},   # Purpose 7: Both Consent and LI
                "8": {"C": True, "LI": False},  # Purpose 8: Only Consent
                "9": {"C": True, "LI": True},   # Purpose 9: Both Consent and LI
                "10": {"C": True, "LI": True},  # Purpose 10: Both Consent and LI
            }
            
            purposes_data.append({
                "id": purpose_id,
                "name": purpose_info.get('name', ''),
                "description": purpose_info.get('description', ''),
                "consentAllowed": framework_allows.get(purpose_id, {}).get("C", False),
                "legitimateInterestAllowed": framework_allows.get(purpose_id, {}).get("LI", False)
            })
        
        # Extract vendors data
        vendors_data = []
        for vendor_id, vendor_info in data.get('vendors', {}).items():
            # Get the vendor's purposes and legIntPurposes
            purposes = [str(p) for p in vendor_info.get('purposes', [])]
            leg_int_purposes = [str(p) for p in vendor_info.get('legIntPurposes', [])]
            flexible_purposes = [str(p) for p in vendor_info.get('flexiblePurposes', [])]
            special_purposes = [str(p) for p in vendor_info.get('specialPurposes', [])]
            features = [str(f) for f in vendor_info.get('features', [])]
            special_features = [str(f) for f in vendor_info.get('specialFeatures', [])]
            
            # Calculate purpose values
            purpose_values = {}
            for i in range(1, 11):
                purpose_str = str(i)
                
                # Check if the purpose is in the vendor's purposes list
                has_consent = purpose_str in purposes
                
                # Check if the purpose is in the vendor's legIntPurposes list
                has_leg_int = purpose_str in leg_int_purposes
                
                # Check if the purpose is in the vendor's flexiblePurposes list
                is_flexible = purpose_str in flexible_purposes
                
                # Determine the value based on the combination
                if has_consent and has_leg_int:
                    purpose_values[f"p{i}"] = 3  # Both Consent and LI
                elif has_consent and is_flexible:
                    purpose_values[f"p{i}"] = 3  # Both Consent and LI (flexible)
                elif has_leg_int and is_flexible:
                    purpose_values[f"p{i}"] = 3  # Both Consent and LI (flexible)
                elif has_consent:
                    purpose_values[f"p{i}"] = 1  # Consent only
                elif has_leg_int:
                    purpose_values[f"p{i}"] = 2  # LI only
                else:
                    purpose_values[f"p{i}"] = 0  # Not used
            
            # Calculate special purpose values
            sp1_value = 1 if "1" in special_purposes else 0
            sp2_value = 1 if "2" in special_purposes else 0
            
            # Calculate feature values
            f1_value = 1 if "1" in features else 0
            f2_value = 1 if "2" in features else 0
            f3_value = 1 if "3" in features else 0
            
            # Calculate special feature values
            sf1_value = 1 if "1" in special_features else 0
            sf2_value = 1 if "2" in special_features else 0
            
            # Get saved vendor status and types
            saved_vendor_data = vendor_data["vendors"].get(vendor_id, {})
            status = saved_vendor_data.get("status", "")
            vendor_types = saved_vendor_data.get("types", [])
            
            vendors_data.append({
                "id": vendor_id,
                "name": vendor_info.get('name', ''),
                "purposes": purposes,
                "legIntPurposes": leg_int_purposes,
                "flexiblePurposes": flexible_purposes,
                "specialPurposes": special_purposes,
                "features": features,
                "specialFeatures": special_features,
                "p1": purpose_values.get("p1", 0),
                "p2": purpose_values.get("p2", 0),
                "p3": purpose_values.get("p3", 0),
                "p4": purpose_values.get("p4", 0),
                "p5": purpose_values.get("p5", 0),
                "p6": purpose_values.get("p6", 0),
                "p7": purpose_values.get("p7", 0),
                "p8": purpose_values.get("p8", 0),
                "p9": purpose_values.get("p9", 0),
                "p10": purpose_values.get("p10", 0),
                "sp1": sp1_value,
                "sp2": sp2_value,
                "f1": f1_value,
                "f2": f2_value,
                "f3": f3_value,
                "sf1": sf1_value,
                "sf2": sf2_value,
                "status": status,
                "vendorTypes": vendor_types
            })
        
        # Sort vendors by ID
        vendors_data.sort(key=lambda x: int(x['id']))
        
        return render_template('vendorlist.html', vendors=vendors_data, purposes=purposes_data)
    
    except requests.exceptions.RequestException as e:
        # Handle request errors
        error_message = f"Error fetching vendor list: {str(e)}"
        return render_template('vendorlist.html', vendors=[], purposes=[], error=error_message)

@app.route('/purposeslist')
def purposeslist():
    try:
        # Fetch the vendor list from the IAB TCF API
        response = requests.get('https://vendor-list.consensu.org/v2/vendor-list.json')
        response.raise_for_status()
        
        data = response.json()
        
        # Extract purposes
        purposes = []
        for purpose_id, purpose_info in data.get('purposes', {}).items():
            # Determine what the framework allows for this purpose
            framework_allows = {
                "1": {"C": True, "LI": False},  # Purpose 1: Only Consent
                "2": {"C": True, "LI": True},   # Purpose 2: Both Consent and LI
                "3": {"C": True, "LI": True},   # Purpose 3: Both Consent and LI
                "4": {"C": True, "LI": True},   # Purpose 4: Both Consent and LI
                "5": {"C": True, "LI": False},  # Purpose 5: Only Consent
                "6": {"C": True, "LI": False},  # Purpose 6: Only Consent
                "7": {"C": True, "LI": True},   # Purpose 7: Both Consent and LI
                "8": {"C": True, "LI": False},  # Purpose 8: Only Consent
                "9": {"C": True, "LI": True},   # Purpose 9: Both Consent and LI
                "10": {"C": True, "LI": True},  # Purpose 10: Both Consent and LI
            }
            
            purposes.append({
                "id": purpose_id,
                "name": purpose_info.get('name', ''),
                "description": purpose_info.get('description', ''),
                "consentAllowed": framework_allows.get(purpose_id, {}).get("C", False),
                "legitimateInterestAllowed": framework_allows.get(purpose_id, {}).get("LI", False)
            })
        
        # Sort purposes by ID
        purposes.sort(key=lambda x: int(x['id']))
        
        # Extract special purposes
        special_purposes = []
        for purpose_id, purpose_info in data.get('specialPurposes', {}).items():
            special_purposes.append({
                "id": purpose_id,
                "name": purpose_info.get('name', ''),
                "description": purpose_info.get('description', '')
            })
        
        # Sort special purposes by ID
        special_purposes.sort(key=lambda x: int(x['id']))
        
        # Extract features
        features = []
        for feature_id, feature_info in data.get('features', {}).items():
            features.append({
                "id": feature_id,
                "name": feature_info.get('name', ''),
                "description": feature_info.get('description', '')
            })
        
        # Sort features by ID
        features.sort(key=lambda x: int(x['id']))
        
        # Extract special features
        special_features = []
        for feature_id, feature_info in data.get('specialFeatures', {}).items():
            special_features.append({
                "id": feature_id,
                "name": feature_info.get('name', ''),
                "description": feature_info.get('description', '')
            })
        
        # Sort special features by ID
        special_features.sort(key=lambda x: int(x['id']))
        
        return render_template('purposeslist.html', 
                              purposes=purposes, 
                              specialPurposes=special_purposes,
                              features=features,
                              specialFeatures=special_features)
    
    except requests.exceptions.RequestException as e:
        # Handle request errors
        error_message = f"Error fetching purposes list: {str(e)}"
        return render_template('purposeslist.html', 
                              purposes=[], 
                              specialPurposes=[],
                              features=[],
                              specialFeatures=[],
                              error=error_message)

if __name__ == '__main__':
    app.run(debug=True, port=5001)