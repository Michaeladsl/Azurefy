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

def check_trusted_named_locations(output):
    """Checks if any named location has the IsTrusted parameter set to True and displays the full output."""
    print(f"{YELLOW}Checking IP ranges location settings for trusted configurations...{RESET}")
    print(f"{CYAN}____________________________________________________{RESET}")
    print()

    

    
    if not output:
        print(f"{RED}No output retrieved from PowerShell. Cannot determine compliance.{RESET}")
        print(f"\n{CYAN}Final Status: {RED}Fail{RESET}")
        return

    is_trusted_found = False
    for line in output.splitlines():
        if "IsTrusted" in line:
            parts = line.split(":")
            if len(parts) > 1:
                value = parts[1].strip().lower()  
                if value == "true":
                    is_trusted_found = True
                    break

    if is_trusted_found:
        print(f"{GREEN}At least one Named Location is marked as Trusted.{RESET}")
        print(f"\n{CYAN}Final Status: {GREEN}Pass{RESET}")
    else:
        print(f"{RED}No Named Location is marked as Trusted.{RESET}")
        print(f"\n{CYAN}Final Status: {RED}Fail{RESET}")

def main():
    """Main function to check compliance for IP ranges location settings."""
    
    commands = [
        
        "Get-MgIdentityConditionalAccessNamedLocation | Format-List"  
    ]

    
    output = run_powershell_tmux(commands)

    
    check_trusted_named_locations(output)

if __name__ == "__main__":
    main()
