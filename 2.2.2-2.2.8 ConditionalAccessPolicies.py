import subprocess
import requests
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


def get_access_token():
    command = "az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv"
    try:
        token, error = run_command(command)
        if token:
            return token
        else:
            print(f"{Fore.RED}Failed to obtain access token via Azure CLI.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error while obtaining access token: {str(e)}{Style.RESET_ALL}")
    return None


def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, str(e)


def get_user_or_spn_email(user_id, token):
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    
    user_response = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers)
    if user_response.status_code == 200:
        user_data = user_response.json()
        return user_data.get('mail', "Email Not Available")
    
    
    spn_response = requests.get(f"https://graph.microsoft.com/v1.0/servicePrincipals/{user_id}", headers=headers)
    if spn_response.status_code == 200:
        spn_data = spn_response.json()
        return spn_data.get('displayName', "SPN Name Not Available")
    
    return "ID Not Found"


def get_group_name(group_id, token):
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    group_response = requests.get(f"https://graph.microsoft.com/v1.0/groups/{group_id}", headers=headers)
    if group_response.status_code == 200:
        group_data = group_response.json()
        return group_data.get('displayName', "Group Name Not Available")
    else:
        return "Group Name Not Available"


def fetch_directory_roles(token):
    directory_roles = {}
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    response = requests.get("https://graph.microsoft.com/v1.0/directoryRoles", headers=headers)
    if response.status_code == 200:
        roles_data = response.json()
        for role in roles_data.get('value', []):
            directory_roles[role['id']] = role['displayName']
    return directory_roles


def color_text(text, color):
    color_dict = {
        "green": Fore.GREEN,
        "red": Fore.RED
    }
    return f"{color_dict.get(color, Fore.RESET)}{text}{Style.RESET_ALL}"


def handle_session_controls(session_controls):
    persistent_browser = session_controls.get('persistentBrowser')
    signIn_frequency = session_controls.get('signInFrequency')
    print(f"  Persistent Browser: {color_text('Set' if persistent_browser else 'None', 'green' if persistent_browser else 'red')}")
    
    if signIn_frequency:
        freq_value = signIn_frequency.get('value')
        freq_type = signIn_frequency.get('type')
        print(f"  Sign-In Frequency: {color_text(f'{freq_value} every {freq_type}', 'green' if freq_value else 'red')}")


def handle_conditions(conditions, token, directory_roles):
    include_users = conditions.get('users', {}).get('includeUsers', [])
    exclude_users = conditions.get('users', {}).get('excludeUsers', [])
    include_groups = conditions.get('users', {}).get('includeGroups', [])
    exclude_groups = conditions.get('users', {}).get('excludeGroups', [])
    include_roles = conditions.get('users', {}).get('includeRoles', [])
    exclude_roles = conditions.get('users', {}).get('excludeRoles', [])
    
    
    if any(user.lower() == "all" for user in include_users):
        print(f"  Include Users: {color_text('ALL', 'green')}")
    else:
        print(f"  Include Users: {[get_user_or_spn_email(uid, token) for uid in include_users]}")

    print(f"  Exclude Users: {[get_user_or_spn_email(uid, token) for uid in exclude_users]}")
    print(f"  Include Groups: {[get_group_name(gid, token) for gid in include_groups]}")
    print(f"  Exclude Groups: {[get_group_name(gid, token) for gid in exclude_groups]}")
    print(f"  Include Roles: {[directory_roles.get(role_id, 'Role Not Found') for role_id in include_roles]}")
    print(f"  Exclude Roles: {[directory_roles.get(role_id, 'Role Not Found') for role_id in exclude_roles]}")
    
    user_risk_levels = conditions.get('userRiskLevels', [])
    sign_in_risk_levels = conditions.get('signInRiskLevels', [])
    print(f"  User Risk Levels: {color_text(str(user_risk_levels), 'green' if user_risk_levels else 'red')}")
    print(f"  Sign-In Risk Levels: {color_text(str(sign_in_risk_levels), 'green' if sign_in_risk_levels else 'red')}")
    
    locations = conditions.get('locations', [])
    print(f"  Locations: {color_text(str(locations), 'green' if locations else 'red')}")


def display_conditional_access_policies(token):
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }

    
    directory_roles = fetch_directory_roles(token)

    
    response = requests.get("https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies", headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}Failed to fetch conditional access policies.{Style.RESET_ALL}")
        return

    policies = response.json()
    for policy in policies.get('value', []):
        grant_controls = policy.get("grantControls") or {}
        conditions = policy.get("conditions", {})
        state = policy.get("state")
        state_color = "green" if state == "enabled" else "red"
        session_controls = policy.get("sessionControls") or {}

        print(f"Policy Name: {color_text(policy.get('displayName', 'N/A'), 'green')}")
        print(f"State: {color_text(state, state_color)}")
        print("Session Controls:")
        handle_session_controls(session_controls)
        print("Conditions:")
        handle_conditions(conditions, token, directory_roles)
        print("\n----------------------------------------\n")


token = get_access_token()
if token:
    display_conditional_access_policies(token)
else:
    print(f"{Fore.RED}Authentication failed. Could not retrieve token.{Style.RESET_ALL}")
