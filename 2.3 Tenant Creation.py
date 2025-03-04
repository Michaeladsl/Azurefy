import subprocess
import tempfile
import time
import os


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
        return False
    return True

def run_powershell_tmux(commands):
    """Runs PowerShell commands in the tmux PowerShell session and captures output via a temp file."""
    try:
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file_path = temp_file.name

        
        for command in commands[:-1]:  
            if not send_command_to_tmux(command):
                return None

        
        final_command = f"{commands[-1]} | Out-File -FilePath {temp_file_path} -Append"
        if not send_command_to_tmux(final_command):
            return None

        
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

def display_formatted_output(output):
    """Displays formatted output according to specified colors and determines final status."""
    print(f"\n{YELLOW}Checking AllowedToCreateTenants settings...{RESET}\n")
    print(f"{CYAN}____________________________________________________{RESET}")
    print()

    allowed_to_create_tenants = None  

    for line in output.splitlines():
        if ":" in line:
            
            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip()

            
            print(f"{BLUE}{key}{RESET} : ", end="")

            
            if key.lower() == "allowedtocreatetenants":
                allowed_to_create_tenants = value.lower()  

                
                if allowed_to_create_tenants == "false":
                    print(f"{GREEN}{value}{RESET}")
                elif allowed_to_create_tenants == "true":
                    print(f"{RED}{value}{RESET}")
            else:
                
                print(f"{MAGENTA}{value}{RESET}")

    
    print("\n" + "-" * 40)
    if allowed_to_create_tenants == "false":
        print(f"{CYAN}Final Status: {GREEN}Pass{RESET}")
    elif allowed_to_create_tenants == "true":
        print(f"{CYAN}Final Status: {RED}Fail{RESET}")
    else:
        print(f"{RED}Final Status: Could not determine compliance (Missing AllowedToCreateTenants value).{RESET}")

def main():
    
    commands = [
        
        
        "Get-MgPolicyAuthorizationPolicy | Select-Object -ExpandProperty DefaultUserRolePermissions | Format-List"  
    ]
    
    
    output = run_powershell_tmux(commands)

    
    if output:
        display_formatted_output(output)
    else:
        print(f"{RED}Failed to retrieve output from PowerShell session.{RESET}")

if __name__ == "__main__":
    main()
