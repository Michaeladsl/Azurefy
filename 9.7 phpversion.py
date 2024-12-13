import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


supported_php_versions = ["PHP|7.4", "PHP|8.0", "PHP|8.1"]

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

def check_php_version(resource_group, app_name):
    """Checks the PHP version of an App Service."""
    command = f'az webapp config show --resource-group {resource_group} --name {app_name} --query "{{LinuxFxVersion:linuxFxVersion,PHP_Version:phpVersion}}" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            config = json.loads(output)
            php_version = config.get("PHP_Version")
            return php_version, output  
        except json.JSONDecodeError:
            return None, None
    return None, None

def display_php_version_status(app_name, php_version, raw_output):
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    """Displays the PHP version status based on the retrieved configuration."""
    if not php_version:  
        print(f"{app_name} - {Fore.GREEN}PHP not in use{Style.RESET_ALL}")
    elif php_version in supported_php_versions:
        print(f"{app_name} - {Fore.GREEN}Supported PHP version: {php_version}{Style.RESET_ALL}")
    else:
        print(f"{app_name} - {Fore.RED}Unsupported PHP version: {php_version}{Style.RESET_ALL}")
    
    
    if raw_output:
        print(f"{Fore.CYAN}\n{raw_output}{Style.RESET_ALL}")

def check_app_service_php_version(subscription_id, subscription_name):
    """Checks if App Services in the current subscription are using a supported PHP version."""
    print(f"\n{Fore.YELLOW}Checking App Services in subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return

    
    app_services = list_app_services()
    if not app_services:
        print(f"{Fore.YELLOW}No App Services found in subscription {subscription_name}.{Style.RESET_ALL}")
        return

    
    subscription_compliant = True

    
    for app in app_services:
        app_name = app["name"]
        resource_group = app["resourceGroup"]

        php_version, raw_output = check_php_version(resource_group, app_name)
        display_php_version_status(app_name, php_version, raw_output)

        
        if php_version and php_version not in supported_php_versions:
            subscription_compliant = False

    
    if subscription_compliant:
        print(f"{Fore.GREEN}\nFinal Status: PASS{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}\nFinal Status: FAIL{Style.RESET_ALL}")

def main():
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        check_app_service_php_version(subscription_id, subscription_name)

if __name__ == "__main__":
    main()
