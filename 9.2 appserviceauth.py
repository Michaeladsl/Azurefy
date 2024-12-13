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
            print(f"{Fore.RED}Error parsing App Services JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve App Services. Error: {error}{Style.RESET_ALL}")
    return []

def check_app_service_auth(resource_group, app_name):
    """Checks the App Service authentication status."""
    command = f'az webapp auth show --resource-group {resource_group} --name {app_name} --output json'
    output, error = run_command(command)
    
    if output:
        try:
            auth_settings = json.loads(output)
            auth_enabled = auth_settings.get("enabled", False)
            return auth_enabled, auth_settings
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing authentication settings for {app_name}.{Style.RESET_ALL}")
            return None, None
    else:
        print(f"{Fore.RED}Failed to retrieve authentication settings for {app_name}. Error: {error}{Style.RESET_ALL}")
    return None, None

def check_basic_auth_publishing(resource_group, app_name):
    """Checks if basic publishing credentials (scm and ftp) are disabled."""
    scm_command = f'az resource show --resource-group {resource_group} --name scm --namespace Microsoft.Web --resource-type basicPublishingCredentialsPolicies --parent sites/{app_name} --output json'
    ftp_command = f'az resource show --resource-group {resource_group} --name ftp --namespace Microsoft.Web --resource-type basicPublishingCredentialsPolicies --parent sites/{app_name} --output json'

    scm_output, _ = run_command(scm_command)
    ftp_output, _ = run_command(ftp_command)

    scm_disabled, ftp_disabled = False, False
    scm_json, ftp_json = None, None

    if scm_output:
        try:
            scm_json = json.loads(scm_output)
            scm_disabled = scm_json.get("properties", {}).get("allow", True) == False
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing SCM publishing credentials for {app_name}.{Style.RESET_ALL}")

    if ftp_output:
        try:
            ftp_json = json.loads(ftp_output)
            ftp_disabled = ftp_json.get("properties", {}).get("allow", True) == False
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing FTP publishing credentials for {app_name}.{Style.RESET_ALL}")

    return scm_disabled, ftp_disabled, scm_json, ftp_json

def check_app_service_compliance(subscription_id, subscription_name):
    """Checks if App Services in the current subscription are compliant with authentication and basic auth publishing credentials settings."""
    print(f"\n{Fore.CYAN}Checking App Services in subscription: {subscription_name}{Style.RESET_ALL}")

    if not set_subscription(subscription_id):
        return

    app_services = list_app_services()
    if not app_services:
        print(f"{Fore.YELLOW}No App Services found in subscription {subscription_name}.{Style.RESET_ALL}")
        return

    for app in app_services:
        app_name = app["name"]
        resource_group = app["resourceGroup"]

        auth_enabled, auth_settings = check_app_service_auth(resource_group, app_name)
        scm_disabled, ftp_disabled, scm_json, ftp_json = check_basic_auth_publishing(resource_group, app_name)

        if auth_enabled and scm_disabled and ftp_disabled:
            print(f"{Fore.GREEN}App Service compliant: {app_name}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}App Service non-compliant: {app_name}{Style.RESET_ALL}")
            if not auth_enabled:
                print(f"{Fore.RED}Authentication Settings: {json.dumps(auth_settings, indent=4)}{Style.RESET_ALL}")
            if not scm_disabled:
                print(f"{Fore.RED}SCM Publishing Settings: {json.dumps(scm_json, indent=4)}{Style.RESET_ALL}")
            if not ftp_disabled:
                print(f"{Fore.RED}FTP Publishing Settings: {json.dumps(ftp_json, indent=4)}{Style.RESET_ALL}")

def main():
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        check_app_service_compliance(subscription_id, subscription_name)

if __name__ == "__main__":
    main()
