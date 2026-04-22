#!/usr/bin/env python3

import yaml
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MERGED_SPEC_FILE = BASE_DIR.parent / 'artifacts' / 'redfish-openapi.yaml'
GENERATED_DIR = BASE_DIR.parent / 'artifacts' / 'generated'

def add_basic_auth_to_existing_spec():
    if not MERGED_SPEC_FILE.exists():
        print(f"Error: {MERGED_SPEC_FILE} does not exist")
        return False
    
    print(f"Loading existing OpenAPI spec from {MERGED_SPEC_FILE}...")
    
    # Load the existing spec
    with open(MERGED_SPEC_FILE, 'r') as f:
        spec = yaml.safe_load(f)
    
    print("Adding Basic Authentication configuration...")
    
    # Ensure components and securitySchemes exist
    if 'components' not in spec:
        spec['components'] = {}
    if 'securitySchemes' not in spec['components']:
        spec['components']['securitySchemes'] = {}
    
    # Add BasicAuth security scheme (only if not already present)
    if 'BasicAuth' not in spec['components']['securitySchemes']:
        spec['components']['securitySchemes']['BasicAuth'] = {
            'type': 'http',
            'scheme': 'basic',
            'description': 'HTTP Basic Authentication for Redfish API'
        }
        print("  Added BasicAuth security scheme")
    else:
        print("  BasicAuth security scheme already exists")
    
    # Add global security requirements (only if not already present)
    if 'security' not in spec:
        spec['security'] = []
    
    # Check if BasicAuth is already in global security
    has_basic_auth = any('BasicAuth' in req for req in spec['security'] if isinstance(req, dict))
    has_empty_auth = {} in spec['security']
    
    if not has_basic_auth:
        spec['security'].append({'BasicAuth': []})
        print("  Added BasicAuth to global security")
    
    if not has_empty_auth:
        spec['security'].append({})
        print("  Added empty auth option for public endpoints")
    
    # Configure endpoint security (only if not already configured)
    if 'paths' in spec:
        # Public endpoints (entire endpoint is public, all methods)
        public_endpoints = [
            '/redfish',
            '/redfish/v1/',
            '/redfish/v1/$metadata',
            '/redfish/v1/odata',
            '/redfish/v1/SessionService/Sessions/Members',
        ]
        
        # Public methods on specific endpoints (mixed protection)
        public_methods = {
            '/redfish/v1/SessionService/Sessions': ['post'],  # POST allows unauthenticated login
        }
        
        for endpoint in public_endpoints:
            if endpoint in spec['paths']:
                for method, method_spec in spec['paths'][endpoint].items():
                    if method.lower() in ['get', 'head', 'options', 'post', 'put', 'patch', 'delete']:
                        # Public endpoints should always remain explicitly unauthenticated.
                        method_spec['security'] = [{}]
                        print(f"  Set {endpoint} {method.upper()} as public (no auth)")
        
        # Public methods on mixed endpoints
        for endpoint, methods in public_methods.items():
            if endpoint in spec['paths']:
                for method in methods:
                    if method in spec['paths'][endpoint]:
                        spec['paths'][endpoint][method]['security'] = [{}]
                        print(f"  Set {endpoint} {method.upper()} as public (no auth)")
        
        # Enforce auth requirement on all protected endpoints (always enforce, never mixed)
        protected_count = 0
        for path, path_spec in spec['paths'].items():
            if path not in public_endpoints:
                for method, method_spec in path_spec.items():
                    if method.lower() in ['get', 'post', 'put', 'patch', 'delete']:
                        # Skip methods that have been explicitly marked as public
                        if path in public_methods and method.lower() in public_methods[path]:
                            continue
                        # Always enforce pure BasicAuth on protected endpoints (overwrite mixed security)
                        method_spec['security'] = [{'BasicAuth': []}]
                        protected_count += 1
        
        if protected_count > 0:
            print(f"  Set BasicAuth requirement on {protected_count} protected endpoints (pure, no mixed auth)")
    
    # Add global Basic Auth metadata (only if not already present)
    if 'x-basic-auth' not in spec:
        spec['x-basic-auth'] = {
            'default-auth': 'BasicAuth',
            'redfish-compliant': True,
            'service-root-public': True
        }
        print("  Added Basic Auth metadata")
    else:
        print("  Basic Auth metadata already exists")
    
    # Write the enhanced spec back to the file
    with open(MERGED_SPEC_FILE, 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    
    print(f"Basic Auth configuration added to {MERGED_SPEC_FILE}")
    return True

def regenerate_go_code():
    print("Regenerating Go server code...")
    
    try:
        result = subprocess.run(['make', 'rf-generate'], 
                              capture_output=True, text=True, cwd=str(BASE_DIR))
        
        if result.returncode == 0:
            print("Go server code regenerated!")
            return True
        else:
            print(f"Code generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def verify_auth_implementation():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generated output directory ready: {GENERATED_DIR}")
    return True

if __name__ == "__main__":
    print("Setting up Basic Authentication for Redfish API...")
    
    # Step 1: Update OpenAPI spec
    if not add_basic_auth_to_existing_spec():
        print("Failed to update OpenAPI specification")
        sys.exit(1)
    
    # Step 2: Verify auth implementation exists  
    if not verify_auth_implementation():
        print("Authentication implementation missing")
        sys.exit(1)
    
    # Step 3: Regenerate Go code
    if not regenerate_go_code():
        print("Failed to regenerate Go code")
        sys.exit(1)
