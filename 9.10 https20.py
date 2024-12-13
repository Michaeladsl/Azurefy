import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, str(e)

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}'"
    output, error = run_command(command)
    
    if output:
        try:
            subscriptions = json.loads(output)
            return subscriptions if subscriptions else []
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions. Error: {error}{Style.RESET_ALL}")
    return []

def set_subscription(subscription_id):
    """Sets the current Azure subscription."""
    command = f'az account set --subscription {subscription_id}'
    output, error = run_command(command)
    if error:
        print(f"{Fore.RED}Failed to set subscription {subscription_id}. Error: {error}{Style.RESET_ALL}")
    return output is not None

def list_app_services():
    """Lists all App Services (Web Apps) in the current subscription."""
    command = "az webapp list --query '[].{name:name, resourceGroup:resourceGroup}' --output json"
    output, error = run_command(command)
    
    if output:
        try:
            apps = json.loads(output)
            return apps if apps else []
        except json.JSONDecodeError:
            return []
    return []

def check_http2_status(resource_group, app_name):
    """Checks if HTTP 2.0 is enabled for an App Service."""
    command = f'az webapp config show --resource-group {resource_group} --name {app_name} --query http20Enabled --output json'
    output, error = run_command(command)
    
    if output is not None:
        try:
            http2_enabled = json.loads(output)
            return http2_enabled
        except json.JSONDecodeError:
            return None
    return None

def display_http2_status(app_name, http2_enabled, non_compliant_apps):
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    """Displays HTTP 2.0 status for the given App Service and adds non-compliant apps to the list."""
    if http2_enabled is True:
        print(f"{Fore.GREEN}HTTP 2.0 enabled for App Service: {app_name}{Style.RESET_ALL}")
    elif http2_enabled is False:
        print(f"{Fore.RED}HTTP 2.0 disabled for App Service: {app_name}{Style.RESET_ALL}")
        non_compliant_apps.append(app_name)
    else:
        print(f"{Fore.YELLOW}HTTP 2.0 status unknown for App Service: {app_name}{Style.RESET_ALL}")

def check_app_service_http2(subscription_id, subscription_name):
    """Checks if App Services in the current subscription have HTTP 2.0 enabled."""
    print(f"\n{Fore.YELLOW}Checking HTTP 2.0 status in App Services for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return "PASS"

    
    app_services = list_app_services()
    if not app_services:
        print(f"{Fore.YELLOW}No App Services found in subscription {subscription_name}.{Style.RESET_ALL}")
        return "PASS"

    non_compliant_apps = []

    
    for app in app_services:
        app_name = app["name"]
        resource_group = app["resourceGroup"]

        http2_enabled = check_http2_status(resource_group, app_name)
        display_http2_status(app_name, http2_enabled, non_compliant_apps)

    if non_compliant_apps:
        print(f"\n{Fore.RED}Non-compliant App Services in subscription {subscription_name}:{Style.RESET_ALL}")
        print(json.dumps(non_compliant_apps, indent=4))
        return "FAIL"
    return "PASS"

def main():
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        final_status = check_app_service_http2(subscription_id, subscription_name)

        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if final_status == 'PASS' else Fore.RED}{final_status}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
