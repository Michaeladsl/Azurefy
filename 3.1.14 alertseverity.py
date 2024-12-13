import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION = "2020-01-01-preview"

def run_command(command):
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = process.stdout.strip()
        return result if result else 'null'
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Command failed: {e}{Style.RESET_ALL}")
        return 'null'

def get_subscriptions_and_tokens():
    command = 'az account get-access-token --query "{subscription:subscription,accessToken:accessToken}" -o tsv'
    result = run_command(command)
    if result == 'null':
        print(f"{Fore.RED}Failed to retrieve subscriptions and tokens.{Style.RESET_ALL}")
        return []
    
    subscriptions = []
    for line in result.splitlines():
        try:
            subscription, token = line.split("\t")
            subscriptions.append({"subscription": subscription, "token": token})
        except ValueError:
            print(f"{Fore.RED}Invalid line in subscription/token output: {line}{Style.RESET_ALL}")
    return subscriptions

def get_security_contacts(subscription, token):
    url = f"{RESOURCE}/subscriptions/{subscription}/providers/Microsoft.Security/securityContacts?api-version={API_VERSION}"
    command = f'curl -s -X GET -H "Authorization: Bearer {token}" -H "Content-Type:application/json" "{url}"'
    response = run_command(command)
    if response == 'null':
        print(f"{Fore.RED}Failed to retrieve security contacts for subscription {subscription}.{Style.RESET_ALL}")
        return None
    try:
        contacts = json.loads(response)
        print(f"\n{Fore.YELLOW}Check for Security Contact:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}_____________________________________{Style.RESET_ALL}")
        print()
        print(json.dumps(contacts, indent=4))
        return contacts
    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse security contact response for subscription {subscription}.{Style.RESET_ALL}")
        return None

def process_security_contacts(subscription, contacts):
    if not contacts or "value" not in contacts or not contacts["value"]:
        print(f"{Fore.RED}No security contacts found or response is empty for subscription {subscription}.{Style.RESET_ALL}")
        print(f"\nFinal Status: {Fore.RED}Fail{Style.RESET_ALL}")
        return

    for contact in contacts["value"]:
        if contact.get("name") == "default":
            properties = contact.get("properties", {})
            alert_notifications = properties.get("alertNotifications", {})
            state = alert_notifications.get("state", "Unknown")
            minimal_severity = alert_notifications.get("minimalSeverity", "Unknown")
            
            state_color = Fore.GREEN if state == "On" else Fore.RED
            severity_color = Fore.GREEN if minimal_severity == "High" else Fore.RED

            print()
            print(f"State: {state_color}{state}{Style.RESET_ALL}")
            print(f"Minimal Severity: {severity_color}{minimal_severity}{Style.RESET_ALL}")

            if state == "On" and minimal_severity == "High":
                final_status = f"{Fore.GREEN}Pass{Style.RESET_ALL}"
            else:
                final_status = f"{Fore.RED}Fail{Style.RESET_ALL}"

            print(f"\nFinal Status: {final_status}")
            return

    print(f"{Fore.RED}Default security contact not found for subscription {subscription}.{Style.RESET_ALL}")
    print(f"\nFinal Status: {Fore.RED}Fail{Style.RESET_ALL}")

def main():
    subscriptions = get_subscriptions_and_tokens()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions or tokens retrieved. Exiting.{Style.RESET_ALL}")
        return

    for entry in subscriptions:
        subscription = entry["subscription"]
        token = entry["token"]
        contacts = get_security_contacts(subscription, token)
        if contacts:
            process_security_contacts(subscription, contacts)
        else:
            print(f"{Fore.RED}Skipping subscription {subscription} due to errors retrieving contacts.{Style.RESET_ALL}")
            print(f"\nFinal Status: {Fore.RED}Fail{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
