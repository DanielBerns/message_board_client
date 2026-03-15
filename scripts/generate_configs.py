import yaml
import argparse
import os
import sys

def generate_user_config(user_data, server_url, security_key, output_dir, is_admin=False):
    \"\"\"Generates a config.yaml for a specific user and saves it to the output directory.\"\"\"
    username = user_data.get("username")
    password = user_data.get("password")

    if not username or not password:
        print(f"Skipping user due to missing username or password: {user_data}")
        return

    config_data = {
        "server": {
            "base_url": server_url
        },
        "credentials": {
            "username": username,
            "password": password
        },
        "encryption": {
            "shared_key": security_key
        }
    }

    # Use a descriptive filename, distinguishing admins if necessary
    filename = f"config_client_{username}.yaml"
    if is_admin:
         filename = f"config_admin_{username}.yaml"

    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Generate client config.yaml files from a master YAML definition.")
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Path to the master input YAML file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Path to the directory where generated config files will be stored"
    )

    args = parser.parse_args()

    input_file = args.input
    output_dir = args.output

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(input_file, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        sys.exit(1)

    server_url = data.get("server_url")
    security_key = data.get("security_key")

    if not server_url or not security_key:
        print("Error: 'server_url' or 'security_key' missing from input YAML.")
        sys.exit(1)

    # Process admin user
    admin_data = data.get("admin")
    if admin_data:
        generate_user_config(admin_data, server_url, security_key, output_dir, is_admin=True)
    else:
        print("Warning: No 'admin' user found in input YAML.")

    # Process standard users
    users = data.get("users", [])
    if isinstance(users, list):
        for user_data in users:
            generate_user_config(user_data, server_url, security_key, output_dir)
    else:
        print("Warning: 'users' key in YAML should be a list.")

    print("Configuration file generation complete.")

if __name__ == "__main__":
    main()
