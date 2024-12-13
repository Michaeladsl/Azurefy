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

def list_web_apps(subscription_id):
    """Lists all web apps in the current subscription."""
    command = f'az webapp list --subscription {subscription_id} --query "[].{{name:name, resourceGroup:resourceGroup}}" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            web_apps = json.loads(output)
            return web_apps if web_apps else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing web app list JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.YELLOW}No web apps found in subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_https_only_setting(resource_group, app_name, subscription_id):
    """Checks the HTTPS-only setting of a web app."""
    command = f'az webapp show --resource-group {resource_group} --name {app_name} --subscription {subscription_id} --query httpsOnly --output json'
    output, error = run_command(command)
    
    if output:
        try:
            https_only = json.loads(output)
            return https_only, output
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing HTTPS-only JSON output for app {app_name}.{Style.RESET_ALL}")
            return None, None
    return False, None  

def check_webapp_https_only(subscription_id, subscription_name):
    """Checks if each web app in the subscription has HTTPS-only traffic enabled."""
    print(f"\n{Fore.YELLOW}Checking web apps for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return

    
    web_apps = list_web_apps(subscription_id)
    if not web_apps:
        print(f"{Fore.YELLOW}No web apps found in subscription {subscription_name}.{Style.RESET_ALL}")
        return "PASS"

    
    subscription_compliant = True

    
    for app in web_apps:
        app_name = app['name']
        resource_group = app['resourceGroup']

        https_only, raw_output = check_https_only_setting(resource_group, app_name, subscription_id)
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        if https_only is True:
            print(f"{Fore.GREEN}HTTPS-only traffic enabled for Web App: {app_name}{Style.RESET_ALL}")
        elif https_only is False:
            print(f"{Fore.RED}HTTPS-only traffic not enabled for Web App: {app_name}{Style.RESET_ALL}")
            subscription_compliant = False
        else:
            print(f"{Fore.YELLOW}Unable to determine HTTPS-only setting for Web App: {app_name}{Style.RESET_ALL}")
        
        
        if raw_output:
            print(f"{Fore.CYAN}\n{raw_output}{Style.RESET_ALL}")
    print()
    
    if subscription_compliant:
        print(f"{Fore.GREEN}Final Status: PASS{Style.RESET_ALL}")
        return "PASS"
    else:
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
        check_webapp_https_only(subscription_id, subscription_name)

if __name__ == "__main__":
    main()
