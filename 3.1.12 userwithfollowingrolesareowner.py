import json
import requests
import subprocess
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION = "2020-01-01-preview"

def get_access_token():
    """Retrieve the Azure access token and subscription ID."""
    print(f"\n{Fore.YELLOW}Checking user role ownership...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    command = "az account get-access-token --query '{subscription:subscription,accessToken:accessToken}' -o json"
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
        data = json.loads(result.stdout)
        access_token = data.get("accessToken")
        subscription_id = data.get("subscription")
        if access_token and subscription_id:
            return subscription_id, access_token
        else:
            print(f"{Fore.RED}Failed to retrieve access token or subscription ID.{Style.RESET_ALL}")
            return None, None
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to execute command: {e}{Style.RESET_ALL}")
        return None, None

def get_security_contact(subscription_id, access_token):
    """Fetches the security contact information for the specified subscription using the provided token."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Security/securityContacts?api-version={API_VERSION}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        if isinstance(data, dict) and "value" in data:
            
            data_items = data["value"]
            default_contact = next((item["properties"]["notificationsByRole"]
                                    for item in data_items if item.get("name") == "default"), None)
            print_color_coded_json(data, default_contact)
            return default_contact
        else:
            print(f"{Fore.RED}Unexpected data format for subscription {subscription_id}.{Style.RESET_ALL}")
            print(f"{Fore.RED}Raw response data: {data}{Style.RESET_ALL}")
    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse JSON response.{Style.RESET_ALL}")

    return None

def print_color_coded_json(data, notifications_by_role):
    """Prints JSON data with inline color-coding for state and roles."""
    json_str = json.dumps(data, indent=4)
    all_passed = True  

    
    state_status = False
    role_status = False

    if notifications_by_role:
        
        state = notifications_by_role.get("state", "Unknown")
        state_color = Fore.GREEN if state.lower() == "on" else Fore.RED
        if state.lower() == "on":
            state_status = True
        else:
            all_passed = False
        json_str = json_str.replace(f'"{state}"', f'{state_color}"{state}"{Style.RESET_ALL}')

        
        roles = notifications_by_role.get("roles", [])
        for role in roles:
            role_color = Fore.GREEN if role.lower() == "owner" else Fore.RED
            if role.lower() == "owner":
                role_status = True
            else:
                all_passed = False
            json_str = json_str.replace(f'"{role}"', f'{role_color}"{role}"{Style.RESET_ALL}')

        
        all_passed = state_status and role_status
    else:
        print(f"{Fore.RED}No notifications by role found in the response.{Style.RESET_ALL}")
        all_passed = False

    print(json_str)

    
    print("\n" + ("Final Status: " + (f"{Fore.GREEN}Pass{Style.RESET_ALL}" if all_passed else f"{Fore.RED}Fail{Style.RESET_ALL}")))

def main():
    """Entry point for the script."""
    subscription_id, access_token = get_access_token()
    if subscription_id and access_token:
        get_security_contact(subscription_id, access_token)

if __name__ == "__main__":
    main()
