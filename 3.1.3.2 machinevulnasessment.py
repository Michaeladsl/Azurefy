from colorama import init, Fore, Back, Style
import subprocess
import json
import sys

# Initialize colorama
init(autoreset=True)

def get_subscription_ids():
    try:
        command = ["az", "account", "list", "--query", "[].id", "-o", "json"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        subscription_ids = json.loads(result.stdout)
        return subscription_ids
    except subprocess.CalledProcessError as e:
        print(f"Error fetching subscription IDs: {e.stderr.strip()}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        sys.exit(1)

def generate_links(subscription_ids):
    base_url = "https://portal.azure.com/#view/Microsoft_Azure_Security/DataCollectionBladeV2/subscriptionId/"
    links = [f"{base_url}{sub_id}" for sub_id in subscription_ids]
    return links

def main():
    subscription_ids = get_subscription_ids()

    if not subscription_ids:
        print(
            Back.RED + Fore.WHITE +
            "No subscriptions found. Please ensure you are logged into Azure CLI and have the necessary permissions." +
            Style.RESET_ALL
        )
        sys.exit(0)

    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for 3.1.3.2 Ensure that 'Vulnerability assessment for machines' component status is set to 'On'." +
        Style.RESET_ALL
    )
    additional_info = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Same link can be used for 3.1.3.3, 3.1.3.4, and 3.1.3.5" +
        Style.RESET_ALL
    )
    print(message)
    print(additional_info)

    links = generate_links(subscription_ids)

    box_width = max(len(link) for link in links) + 4
    border = "+" + "-" * (box_width - 2) + "+"

    print(border)
    for link in links:
        print(f"| {link.ljust(box_width - 4)} |")
    print(border)

if __name__ == "__main__":
    main()

