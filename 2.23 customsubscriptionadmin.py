import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def color_text(text, color):
    """Returns text formatted with specified color."""
    color_dict = {
        "green": Fore.GREEN,
        "red": Fore.RED,
        "yellow": Fore.YELLOW
    }
    return f"{color_dict.get(color, Fore.RESET)}{text}{Style.RESET_ALL}"

def run_command(command):
    """Runs a shell command and returns the output as JSON if possible, or an error message."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.loads(process.stdout), None
    except subprocess.CalledProcessError as e:
        return None, f"Command failed: {e.stderr}"
    except json.JSONDecodeError:
        return process.stdout, "Error parsing JSON output"

def list_custom_roles():
    """Lists custom roles and their permissions."""
    custom_roles_command = "az role definition list --custom-role-only True"
    custom_roles, error = run_command(custom_roles_command)
    
    if error:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        return None

    if not custom_roles:
        print(f"{Fore.GREEN}No custom subscription administrative roles found.{Style.RESET_ALL}")
        return []

    for role in custom_roles:
        role_name = role.get('roleName')
        permissions = role.get('permissions', [])
        print(f"{Fore.YELLOW}Role Name: {role_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Permissions: {json.dumps(permissions, indent=4)}{Style.RESET_ALL}")
    
    return custom_roles

def check_custom_roles():
    """Checks if custom subscription administrative roles exist and prints final status."""
    print(f"{Fore.YELLOW}Checking for custom subscription administrative roles...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    custom_roles = list_custom_roles()

    if not custom_roles:
        print(f"{Fore.GREEN}Final Status: PASS{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Final Status: FAIL{Style.RESET_ALL}")

def main():
    
    check_custom_roles()

if __name__ == "__main__":
    main()
