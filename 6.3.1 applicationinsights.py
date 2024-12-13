import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)
RESOURCE = "https://management.azure.com"

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e}{Style.RESET_ALL}")
        return None

def get_access_token():
    """Retrieve an access token using Azure CLI."""
    command = 'az account get-access-token --query accessToken -o tsv'
    access_token = run_command(command)
    if access_token:
        print()
    else:
        print(f"{Fore.RED}Failed to retrieve access token. Ensure you are logged in with 'az login'.{Style.RESET_ALL}")
    return access_token

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}'"
    result = run_command(command)
    
    if result:
        try:
            subscriptions = json.loads(result)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    return []

def check_application_insights(subscription_id):
    """Checks if Application Insights is configured for a specific subscription."""
    command = f'az monitor app-insights component show --subscription {subscription_id} --query "[].{{ID:appId, Name:name, Tenant:tenantId, Location:location, Provisioning_State:provisioningState}}" --output json'
    result = run_command(command)

    
    print(result)

    if result:
        try:
            insights_data = json.loads(result)
            if insights_data:
                return True, insights_data
            else:
                return False, None
        except json.JSONDecodeError:
            return False, None
    return False, None

def display_application_insights_status():
    """Iterates through each subscription and checks if Application Insights is configured."""
    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_compliance = True  

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking Application Insights for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        is_configured, insights_data = check_application_insights(subscription_id)

        
        if is_configured:
            print(f"{Fore.GREEN}Application Insights configured for subscription {subscription_name}.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Application Insights missing for subscription {subscription_name}.{Style.RESET_ALL}")
            overall_compliance = False  
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

    
    print("\n")
    if overall_compliance:
        print(f"{Fore.GREEN}Final Status: PASS{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Final Status: FAIL{Style.RESET_ALL}")

def main():
    display_application_insights_status()

if __name__ == "__main__":
    main()
