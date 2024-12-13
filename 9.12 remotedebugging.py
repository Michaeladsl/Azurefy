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

def check_remote_debugging_status(resource_group, app_name):
    """Checks if remote debugging is disabled for an App Service."""
    command = f'az webapp config show --resource-group {resource_group} --name {app_name} --query "{{remoteDebuggingEnabled:remoteDebuggingEnabled}}" -o json'
    output, error = run_command(command)
    
    if output is not None:
        try:
            debugging_status = json.loads(output)
            return debugging_status
        except json.JSONDecodeError:
            return None
    return None

def display_debugging_status(app_name, debugging_status):
    """Displays remote debugging status for the given App Service."""
    remote_debugging_enabled = debugging_status.get("remoteDebuggingEnabled", None)
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    if remote_debugging_enabled is False:
        print(f"{Fore.GREEN}Remote debugging is disabled for App Service: {app_name}{Style.RESET_ALL}")
    elif remote_debugging_enabled is True:
        print(f"{Fore.RED}Remote debugging is enabled for App Service: {app_name}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Remote debugging status unknown for App Service: {app_name}{Style.RESET_ALL}")

    
    print(f"{Fore.CYAN}\n{json.dumps(debugging_status, indent=4)}{Style.RESET_ALL}")

def check_app_service_debugging(subscription_id, subscription_name):
    """Checks if App Services in the current subscription have remote debugging disabled."""
    print(f"\n{Fore.YELLOW}Checking App Services in subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return

    
    app_services = list_app_services()
    if not app_services:
        print(f"{Fore.YELLOW}No App Services found in subscription {subscription_name}.{Style.RESET_ALL}")
        return "PASS"  

    
    subscription_compliant = True

    
    for app in app_services:
        app_name = app["name"]
        resource_group = app["resourceGroup"]

        debugging_status = check_remote_debugging_status(resource_group, app_name)
        if debugging_status:
            remote_debugging_enabled = debugging_status.get("remoteDebuggingEnabled", None)
            display_debugging_status(app_name, debugging_status)

            if remote_debugging_enabled is True:
                subscription_compliant = False  
        else:
            print(f"{Fore.RED}Failed to retrieve remote debugging status for App Service: {app_name}{Style.RESET_ALL}")

    
    if subscription_compliant:
        print()
        print(f"{Fore.GREEN}Final Status: PASS{Style.RESET_ALL}")
        return "PASS"
    else:
        print()
        print(f"{Fore.RED}Final Status: FAIL{Style.RESET_ALL}")
        return "FAIL"

def main():
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        check_app_service_debugging(subscription_id, subscription_name)

if __name__ == "__main__":
    main()
