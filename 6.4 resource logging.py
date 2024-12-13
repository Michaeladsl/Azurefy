import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output and any error encountered."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr

def get_access_token():
    """Retrieve an access token using Azure CLI."""
    command = 'az account get-access-token --query accessToken -o tsv'
    access_token, error = run_command(command)
    if access_token:
        print(f"{Fore.GREEN}Successfully retrieved access token.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve access token. Ensure you are logged in with 'az login'. Error: {error}{Style.RESET_ALL}")
    return access_token

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}'"
    output, error = run_command(command)
    
    if output:
        try:
            subscriptions = json.loads(output)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions. Error: {error}{Style.RESET_ALL}")
    return []

def get_resources(subscription_id):
    """Fetches all resources for a specific subscription."""
    command = f'az resource list --subscription {subscription_id} --output json'
    output, error = run_command(command)
    
    if output:
        try:
            resources = json.loads(output)
            return resources if resources else []
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for resources: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve resources for subscription {subscription_id}. Error: {error}{Style.RESET_ALL}")
    return []

def check_diagnostic_settings(resource_id):
    """Checks if diagnostic settings are configured for a given resource."""
    command = f'az monitor diagnostic-settings list --resource {resource_id} --output json'
    output, error = run_command(command)

    
    resource_name = resource_id.split('/')[-1]
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()

    print(f"{Fore.YELLOW}Diagnostic settings for Resource '{resource_name}':{Style.RESET_ALL}")

    if error and "does not support diagnostic settings" in error:
        print(f"{Fore.YELLOW}Resource: {resource_name} - Logging not supported{Style.RESET_ALL}")
        return 'unsupported', None
    elif output:
        try:
            diagnostic_data = json.loads(output)
            if diagnostic_data:
                return 'configured', diagnostic_data
            else:
                return 'not_configured', None
        except json.JSONDecodeError:
            return 'not_configured', None
    return 'not_configured', None

def display_resource_logging_status():
    """Iterates through each subscription and resource to check if diagnostic settings are configured."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_status = "pass"  

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking resources for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        resources = get_resources(subscription_id)
        if not resources:
            print(f"{Fore.YELLOW}No resources found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for resource in resources:
            resource_name = resource["name"]
            resource_id = resource["id"]
          
            status, data = check_diagnostic_settings(resource_id)

            if status == 'unsupported':
                print(f"Resource: {resource_name} - {Fore.YELLOW}Resource logging not supported{Style.RESET_ALL}")
            elif status == 'not_configured':
                print(f"Resource: {resource_name} - {Fore.RED}Resource logging not configured{Style.RESET_ALL}")
                overall_status = "fail"  
            else:
                print(f"Resource: {resource_name} - {Fore.GREEN}Resource logging configured{Style.RESET_ALL}")

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_status == 'pass' else Fore.RED}{overall_status.upper()}{Style.RESET_ALL}")


def main():
    display_resource_logging_status()

if __name__ == "__main__":
    main()
