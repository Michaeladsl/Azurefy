import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
    print(f"{Fore.YELLOW}Checking for additional emails...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}_____________________________________{Style.RESET_ALL}")
    print(" ")

    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Command failed: {e.stderr}{Style.RESET_ALL}")
        return None


def get_security_contact_emails():
    """Retrieves the security contact emails using the Azure CLI and curl."""
    command = (
        'az account get-access-token --query "{subscription:subscription,accessToken:accessToken}" --out tsv | '
        'xargs -L1 bash -c \'curl -s -X GET -H "Authorization: Bearer $1" -H "Content-Type: application/json" '
        '"https://management.azure.com/subscriptions/$0/providers/Microsoft.Security/securityContacts?api-version=2020-01-01-preview"\' | '
        'jq \'.value[] | select(.name=="default") | .properties.emails\''
    )
    output = run_command(command)
    final_status = "Fail" 

    if output:
        try:
            emails = json.loads(output)
            if emails:
                print(f"{Fore.GREEN}Emails: {emails}{Style.RESET_ALL}")
                final_status = "Pass" 
            else:
                print(f"{Fore.RED}No additional emails configured. Value: null{Style.RESET_ALL}")
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse JSON from the response. Value: null{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Value: null{Style.RESET_ALL}")

    print("\n" + ("Final Status: " + (f"{Fore.GREEN}Pass{Style.RESET_ALL}" if final_status == "Pass" else f"{Fore.RED}Fail{Style.RESET_ALL}")))


def main():
    """Main function to display security contact emails."""
    get_security_contact_emails()

if __name__ == "__main__":
    main()
