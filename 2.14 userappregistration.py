import subprocess
import tempfile
import time
import os
import sys


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

tmux_session_name = "persistent_powershell"

def send_command_to_tmux(command):
    """Send a command to the persistent PowerShell tmux session."""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", tmux_session_name, command, "C-m"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"{RED}Failed to send command to tmux session: {e}{RESET}")
        sys.exit(1)

def run_powershell_tmux(commands):
    """Runs PowerShell commands in the tmux PowerShell session and captures output via a temp file."""
    try:
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file_path = temp_file.name

        
        for command in commands[:-1]:  
            send_command_to_tmux(command)

        
        final_command = f"{commands[-1]} | Out-File -FilePath {temp_file_path} -Append"
        send_command_to_tmux(final_command)

        
        max_retries = 15
        retries = 0
        output_ready = False

        while retries < max_retries:
            time.sleep(1)  
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                output_ready = True
                break
            retries += 1

        if not output_ready:
            print(f"{RED}Error: Output file was not created or remains empty after multiple retries.{RESET}")
            return None

        
        with open(temp_file_path, "r") as file:
            output = file.read().strip()

        

        
        os.remove(temp_file_path)

        return output

    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return None

def display_allowed_to_create_apps(output):
    """Displays the AllowedToCreateApps value with specific formatting and evaluates Pass/Fail."""
    print(f"\n{YELLOW}Checking if users are allowed to create apps...{RESET}")
    print(f"{CYAN}____________________________________________________{RESET}")
    print()

    status = None
    for line in output.splitlines():
        if "AllowedToCreateApps" in line:
            
            parts = line.split(":")
            if len(parts) > 1:
                key = parts[0].strip()
                value = parts[1].strip()

                
                print(f"{BLUE}{key} : {RESET}", end="")

                
                if value.lower() == "false":
                    print(f"{GREEN}{value}{RESET}")
                    status = "Pass"
                elif value.lower() == "true":
                    print(f"{RED}{value}{RESET}")
                    status = "Fail"
                else:
                    print(f"{MAGENTA}{value}{RESET}")

    if status:
        print(f"\n{CYAN}Final Status: {RESET}{status}")
    else:
        print(f"{RED}Unable to determine status. Check the output above.{RESET}")

def run_policy_permissions_check():
    """Main function to check user permissions for policies."""
    commands = [
        "(Get-MgPolicyAuthorizationPolicy).DefaultUserRolePermissions | Format-List AllowedToCreateApps"
    ]
    
    output = run_powershell_tmux(commands)

    
    if output:
        display_allowed_to_create_apps(output)
    else:
        print(f"{RED}Failed to retrieve output from PowerShell session.{RESET}")

def main():
    
    run_policy_permissions_check()

if __name__ == "__main__":
    main()
