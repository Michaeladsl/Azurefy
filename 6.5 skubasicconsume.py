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

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, displayName:name}'"
    output, error = run_command(command)
    
    if output:
        try:
            subscriptions = json.loads(output)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions. Error: {error}{Style.RESET_ALL}")
    return []

def get_resource_groups(subscription_id):
    """Fetches all resource groups for a specific subscription."""
    command = f'az group list --subscription {subscription_id} --query "[].name" -o json'
    output, error = run_command(command)
    
    if output:
        try:
            resource_groups = json.loads(output)
            return resource_groups if resource_groups else []
        except json.JSONDecodeError:
            return []
    return []

def audit_sku(subscription_id, resource_group):
    """Runs a graph query to find resources with 'Basic' or 'consumption' SKUs in a specific resource group."""
    query = f"Resources | where resourceGroup == '{resource_group}' | where sku contains 'Basic' or sku contains 'consumption' | order by type"
    command = f'az graph query -q "{query}" --subscription {subscription_id} -o json'
    output, error = run_command(command)

    if error:
        print(f"{Fore.RED}Failed to run query for resource group {resource_group} in subscription {subscription_id}. Error: {error}{Style.RESET_ALL}")
        return []
    
    if output:
        try:
            resources = json.loads(output)
            non_compliant_resources = [
                resource for resource in resources
                if "sku" in resource and ("Basic" in resource["sku"] or "consumption" in resource["sku"])
            ]
            
            if non_compliant_resources:
                print(f"{Fore.RED}Non-compliant resources found in resource group {resource_group}:{Style.RESET_ALL}")
                for resource in non_compliant_resources:
                    resource_name = resource.get("name", "Unknown")
                    resource_type = resource.get("type", "Unknown")
                    sku = resource.get("sku", "Unknown")
                    print(f"{Fore.RED}Resource: {resource_name}, Type: {resource_type}, SKU: {sku}{Style.RESET_ALL}")
                return non_compliant_resources
            else:
                print(f"{Fore.GREEN}No non-compliant resources found in resource group {resource_group}.{Style.RESET_ALL}")
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing JSON output for resource group {resource_group}.{Style.RESET_ALL}")
    return []

def audit_all_subscriptions():
    """Iterates through each subscription and audits each resource group for non-compliant SKUs."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    overall_status = "pass"  

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.CYAN}Auditing SKUs for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        resource_groups = get_resource_groups(subscription_id)
        if not resource_groups:
            print(f"{Fore.YELLOW}No resource groups found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for resource_group in resource_groups:
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()
            print(f"{Fore.YELLOW}Auditing resource group: {resource_group}{Style.RESET_ALL}")
            non_compliant_resources = audit_sku(subscription_id, resource_group)

            
            if non_compliant_resources:
                overall_status = "fail"

    
    if overall_status == "pass":
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}PASS{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.CYAN}Final Status: {Fore.RED}FAIL{Style.RESET_ALL}")

    
    print("Final Status: PASS" if overall_status == "pass" else "Final Status: FAIL")


def main():
    audit_all_subscriptions()

if __name__ == "__main__":
    main()
