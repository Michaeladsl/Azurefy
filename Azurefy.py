import subprocess
import os
from datetime import datetime
import pty
import sys
import re
from colorama import init, Fore, Style
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import shutil
import argparse
from bs4 import BeautifulSoup

init(autoreset=True)

scripts = [
    '2.1.3 mfaforall.py',
    '2.1.4 remembermfa.py',
    '2.2.1 trusted locations.py',
    '2.2.2-2.2.8 ConditionalAccessPolicies.py',
    '2.3 Tenant Creation.py',
    '2.4 GuestUsers.py',
    '2.5 numberofmethodstoreset.py',
    '2.6 accountlockoutthreshold.py',
    '2.7 accountlockoutduration.py',
    '2.8 bannedpasswordlist.py',
    '2.9 reconfirmauth.py',
    '2.10 userpassresetnotification.py',    
    '2.11 adminpasswordreset.py',
    '2.12 userappconsent.py',
    '2.13 userappconsent.py',
    '2.14 userappregistration.py',
    '2.15 guestaccessrestrictions.py',
    '2.16 guestinvites.py',
    '2.17 entraadmincenteraccess.py',
    '2.18 groupfeatureaccess.py',
    '2.19 securitygroupcreation.py',
    '2.20 grouprequestmanagement.py',
    '2.21 groupscreation.py',
    '2.22 mfarequiredtojoin.py',
    '2.23 customsubscriptionadmin.py',
    '2.25 subingressandegress.py',
    '2.26 globaladmincount.py',
    '3.1.1.1 autoprovisioning.py',
    '3.1.1.2 defendercloudappsint.py',
    '3.1.1.2+defenderforservices.py',
    '3.1.3.2 machinevulnasessment.py',
    '3.1.11 cloudsecbenchmark.py',
    '3.1.12 userwithfollowingrolesareowner.py',
    '3.1.13 additionalemail.py',
    '3.1.14 alertseverity.py',
    '3.3.1 keyvaultRBAC.py',
    '3.3.5 enablepurgeprotectionkeyvault.py',
    '3.3.7 keyvaultprivateendpoints.py',
    '3.3.8 keyvaultkeyroation.py',
    '4.1 Securetransfer.py',
    '4.2 infrastructureencryption.py',
    '4.4 storagekeyrotation.py',
    '4.5 sharedaccesssignature.py',
    '4.6 publicstorageaccess.py',
    '4.7 defaultnetworkaccess.py',
    '4.8 trustedazureservices.py',
    '4.9 privateendpoints.py',
    '4.10 softdelete.py',
    '4.11 critstoragecmk.py',
    '4.12-14 storagelogging.py',
    '4.15 tlsversion.py',
    '4.16 crosstenantreplication.py',
    '4.17 anonymousblobaccess.py',
    '5.1.1 sqlauditing.py',
    '5.1.2 sqlpublicingress.py',
    '5.1.3 sqltdecmk.py',
    '5.2.1 securetransportpostgressql.py',
    '5.2.2 logcheckpointsforpostgressql.py',
    '5.2.3 connectionthrottlepostgresql.py',
    '5.2.4 logfileretention.py',
    '5.2.5 publicaccessTOpostgressql.py',
    '5.2.6 postgreslogconnections.py',
    '5.2.7 logdisconnections.py',
    '5.3.1 mysqlflexsecuretransport.py',
    '5.3.2 sqltlsversion.py',
    '5.3.3 mysqlauditlogenabled.py',
    '5.3.4 mysqlauditlogevents.py',
    '5.4.1 firewallandnetworksaccess.py',
    '6.1.1 diagnostic settings.py',
    '6.1.2 diagsettings categories.py',
    '6.1.3 log container cmk.py',
    '6.1.4 keyvaultlogging.py',
    '6.2.1 activitylogalerts.py',
    '6.3.1 applicationinsights.py',
    '6.4 resource logging.py',
    '6.5 skubasicconsume.py',
    '7.1 rdp access.py',
    '7.2 ssh access.py',
    '7.4 https.py',
    '7.5 nsgretention.py',
    '7.6 network watcher.py',
    '7.7 publicips.py',
    '8.1 bastion.py',
    '8.2 manageddisks.py',
    '8.4 unattacheddiskcmk.py',
    '8.5 disknetworkaccess.py',
    '8.6 dataaccessauth.py',
    '8.7 approvedextensions.py',
    '8.8 endpointprotection.py',
    '8.11 trustedlaunch.py',
    '9.1 httpsonly.py',
    '9.2 appserviceauth.py',
    '9.3 ftpsstate.py',
    '9.4 webapptls.py',
    '9.5 registerwithentraid.py',
    '9.6 webappbasicauth.py',
    '9.7 phpversion.py',
    '9.8 pythonversion.py',
    '9.9 javaversion.py',
    '9.10 https20.py',
    '9.12 remotedebugging.py',
]

script_descriptions = {
    '2.1.3 mfaforall.py': "Ensure that 'Multi-Factor Auth Status' is 'Enabled' for all Non-Privileged Users",
    '2.1.4 remembermfa.py': "Ensure that 'Allow users to remember multi-factor authentication on devices they trust' is Disabled",
    '2.2.1 trusted locations.py': "Ensure Trusted Locations Are Defined",
    '2.2.2-2.2.8 ConditionalAccessPolicies.py': " 2.2.2-2.2.8 review CA policies",
    '2.3 Tenant Creation.py': "2.3 Ensure that 'Restrict non-admin users from creating tenants' is set to 'Yes'",
    '2.4 GuestUsers.py': "2.4 Ensure Guest Users Are Reviewed on a Regular Basis ",
    '2.5 numberofmethodstoreset.py': "2.5 Ensure That 'Number of methods required to reset' is set to '2'",
    '2.6 accountlockoutthreshold.py': "2.6 Ensure that account 'Lockout Threshold' is less than or equal to '10'",
    '2.7 accountlockoutduration.py': "2.7 Ensure that account 'Lockout duration in seconds' is greater than or equal to '60'",
    '2.8 bannedpasswordlist.py': "2.8 Ensure that a Custom Bad Password List is set to 'Enforce' for your Organization",
    '2.9 reconfirmauth.py': "2.9 Ensure that 'Number of days before users are asked to re-confirm their authentication information' is not set to '0'",
    '2.10 userpassresetnotification.py': "2.10 Ensure that 'Notify users on password resets?' is set to 'Yes'",
    '2.11 adminpasswordreset.py': "2.11 Ensure That 'Notify all admins when other admins reset their password?' is set to 'Yes'",
    '2.12 userappconsent.py': "2.12 Ensure User consent for applications is set to Do not allow user consent",
    '2.13 userappconsent.py': "2.13 Ensure 'User consent for applications' Is Set To 'Allow for Verified Publishers'",
    '2.14 userappregistration.py': "2.14 Ensure That 'Users Can Register Applications' Is Set to 'No'",
    '2.15 guestaccessrestrictions.py': "2.15 Ensure That 'Guest users access restrictions' is set to 'Guest user access is restricted to properties and memberships of their own directory objects'",
    '2.16 guestinvites.py': "2.16 Ensure that 'Guest invite restrictions' is set to 'Only users assigned to specific admin roles can invite guest users'",
    '2.17 entraadmincenteraccess.py': "2.17 Ensure That 'Restrict access to Microsoft Entra admin center' is Set to 'Yes'",
    '2.18 groupfeatureaccess.py': "2.18 Ensure that 'Restrict user ability to access groups features in the Access Pane' is Set to 'Yes'",
    '2.19 securitygroupcreation.py': "2.19 Ensure that 'Users can create security groups in Azure portals, API or PowerShell' is set to 'No'",
    '2.20 grouprequestmanagement.py': "2.20 Ensure that 'Owners can manage group membership requests in My Groups' is set to 'No'",
    '2.21 groupscreation.py': "2.21 Ensure that 'Users can create Microsoft 365 groups in Azure portals, API or PowerShell' is set to 'No'",
    '2.22 mfarequiredtojoin.py': "2.22 Ensure that 'Require Multifactor Authentication to register or join devices with Microsoft Entra' is set to 'Yes'",
    '2.23 customsubscriptionadmin.py': "2.23 Ensure That No Custom Subscription Administrator Roles Exist",
    '2.25 subingressandegress.py': "2.25 Ensure That 'Subscription leaving Microsoft Entra tenant' and 'Subscription entering Microsoft Entra tenant' Is Set To 'Permit no one'",
    '2.26 globaladmincount.py': "2.26 Ensure fewer than 5 users have global administrator assignment",
    '3.1.1.1 autoprovisioning.py': "3.1.1.1 Ensure that Auto provisioning of 'Log Analytics agent for Azure VMs' is Set to 'On'",
    '3.1.1.2 defendercloudappsint.py': "3.1.1.2 Ensure that Microsoft Defender for Cloud Apps integration with Microsoft Defender for Cloud is Selected",
    '3.1.1.2+defenderforservices.py': "3.1.3.1 Ensure That Microsoft Defender for Services Is Set to 'On'",
    '3.1.3.2 machinevulnasessment.py': "3.1.3.2 Ensure that 'Vulnerability assessment for machines' component status is set to 'On'",
    '3.1.11 cloudsecbenchmark.py': "3.1.11 Ensure that Microsoft Cloud Security Benchmark policies are not set to 'Disabled'",
    '3.1.12 userwithfollowingrolesareowner.py': "3.1.12 Ensure That 'All users with the following roles' is set to 'Owner'",
    '3.1.13 additionalemail.py': "3.1.13 Ensure 'Additional email addresses' is Configured with a Security Contact Email",
    '3.1.14 alertseverity.py': "3.1.14 Ensure That 'Notify about alerts with the following severity' is Set to 'High'",
    '3.3.1 keyvaultRBAC.py': "3.3.1 Ensure that the Expiration Date is set for all Keys in RBAC Key Vaults",
    '3.3.5 enablepurgeprotectionkeyvault.py': "3.3.5 Ensure the Key Vault is Recoverable",
    '3.3.7 keyvaultprivateendpoints.py': "3.3.7 Ensure that Private Endpoints are Used for Azure Key Vault",
    '3.3.8 keyvaultkeyroation.py': "3.3.8 Ensure Automatic Key Rotation is Enabled Within Azure Key Vault for the Supported Services",
    '4.1 Securetransfer.py': "4.1 Ensure that 'Secure transfer required' is set to 'Enabled'",
    '4.2 infrastructureencryption.py': "4.2 Ensure that 'Enable Infrastructure Encryption' for Each Storage Account in Azure Storage is Set to 'enabled'",
    '4.4 storagekeyrotation.py': "4.4 Ensure that Storage Account Access Keys are Periodically Regenerated",
    '4.5 sharedaccesssignature.py': "4.5 Ensure that Shared Access Signature Tokens Expire Within an Hour",
    '4.6 publicstorageaccess.py': "4.6 Ensure that 'Public Network Access' is 'Disabled' for storage accounts",
    '4.7 defaultnetworkaccess.py': "4.7 Ensure Default Network Access Rule for Storage Accounts is Set to Deny",
    '4.8 trustedazureservices.py': "4.8 Ensure 'Allow Azure services on the trusted services list to access this storage account' is Enabled for Storage Account Access",
    '4.9 privateendpoints.py': "4.9 Ensure Private Endpoints are used to access Storage Accounts",
    '4.10 softdelete.py': "4.10 Ensure Soft Delete is Enabled for Azure Containers and Blob Storage",
    '4.11 critstoragecmk.py': "4.11 Ensure Storage for Critical Data are Encrypted with Customer Managed Keys (CMK)",
    '4.12-14 storagelogging.py': "4.12 Ensure Storage Logging is Enabled for Queue, Blob, and Table Service for 'Read', 'Write', and 'Delete' requests",
    '4.15 tlsversion.py': "4.15 Ensure the 'Minimum TLS version' for storage accounts is set to 'Version 1.2'",
    '4.16 crosstenantreplication.py': "4.16 Ensure 'Cross Tenant Replication' is not enabled",
    '4.17 anonymousblobaccess.py': "4.17 Ensure that 'Allow Blob Anonymous Access' is set to 'Disabled'",
    '5.1.1 sqlauditing.py': "5.1.1 Ensure that 'Auditing' is set to 'On'",
    '5.1.2 sqlpublicingress.py': "5.1.2 Ensure no Azure SQL Databases allow ingress from 0.0.0.0/0 (ANY IP)",
    '5.1.3 sqltdecmk.py': "5.1.3 Ensure SQL server's Transparent Data Encryption (TDE) protector is encrypted with Customer-managed key",
    '5.2.1 securetransportpostgressql.py': "5.2.1 Ensure server parameter 'require_secure_transport' is set to 'ON' for PostgreSQL flexible server",
    '5.2.2 logcheckpointsforpostgressql.py': "5.2.2 Ensure server parameter 'log_checkpoints' is set to 'ON' for PostgreSQL flexible server",
    '5.2.3 connectionthrottlepostgresql.py': "5.2.3 Ensure server parameter 'connection_throttle.enable' is set to 'ON' for PostgreSQL flexible server",
    '5.2.4 logfileretention.py': "5.2.4 Ensure server parameter 'logfiles.retention_days' is greater than 3 days for PostgreSQL flexible server",
    '5.2.5 publicaccessTOpostgressql.py': "5.2.5 Ensure 'Allow public access from any Azure service within Azure to this server' for PostgreSQL flexible server is disabled",
    '5.2.6 postgreslogconnections.py': "5.2.6 [LEGACY] Ensure server parameter 'log_connections' is set to 'ON' for PostgreSQL single server",
    '5.2.7 logdisconnections.py': "5.2.7 [LEGACY] Ensure server parameter 'log_disconnections' is set to 'ON' for PostgreSQL single server",
    '5.3.1 mysqlflexsecuretransport.py': "5.3.1 Ensure server parameter 'require_secure_transport' is set to 'ON' for MySQL flexible server",
    '5.3.2 sqltlsversion.py': "5.3.2 Ensure server parameter 'tls_version' is set to 'TLSv1.2' (or higher) for MySQL flexible server",
    '5.3.3 mysqlauditlogenabled.py': "5.3.3 Ensure server parameter 'audit_log_enabled' is set to 'ON' for MySQL flexible server",
    '5.3.4 mysqlauditlogevents.py': "5.3.4 Ensure server parameter 'audit_log_events' has 'CONNECTION' set for MySQL flexible server",
    '5.4.1 firewallandnetworksaccess.py': "5.4.1 Ensure That 'Firewalls & Networks' Is Limited to Use Selected Networks Instead of All Networks",
    '6.1.1 diagnostic settings.py': "6.1.1 Ensure that a 'Diagnostic Setting' exists for Subscription Activity Logs",
    '6.1.2 diagsettings categories.py': "6.1.2 Ensure Diagnostic Setting captures appropriate categories",
    '6.1.3 log container cmk.py': "6.1.3 Ensure the storage account containing the container with activity logs is encrypted with Customer Managed Key (CMK)",
    '6.1.4 keyvaultlogging.py': "6.1.4 Ensure that logging for Azure Key Vault is 'Enabled'",
    '6.2.1 activitylogalerts.py': "6.2.1 Ensure that Activity Log Alert exists for Create Policy Assignment",
    '6.3.1 applicationinsights.py': "6.3.1 Ensure Application Insights are Configured",
    '6.4 resource logging.py': "6.4 Ensure that Azure Monitor Resource Logging is Enabled for All Services that Support it",
    '6.5 skubasicconsume.py': "6.5 Ensure that SKU Basic/Consumption is not used on artifacts that need to be monitored",
    '7.1 rdp access.py': "7.1 Ensure that RDP access from the Internet is evaluated and restricted",
    '7.2 ssh access.py': "7.2 Ensure that SSH access from the Internet is evaluated and restricted",
    '7.4 https.py': "7.4 Ensure that HTTP(S) access from the Internet is evaluated and restricted",
    '7.5 nsgretention.py': "7.5 Ensure that Network Security Group Flow Log retention period is 'greater than 90 days'",
    '7.6 network watcher.py': "7.6 Ensure that Network Watcher is 'Enabled' for Azure Regions that are in use",
    '7.7 publicips.py': "7.7 Ensure that Public IP addresses are Evaluated on a Periodic Basis",
    '8.1 bastion.py': "8.1 Ensure an Azure Bastion Host Exists",
    '8.2 manageddisks.py': "8.2 Ensure Virtual Machines are utilizing Managed Disks",
    '8.4 unattacheddiskcmk.py': "8.4 Ensure that 'Unattached disks' are encrypted with 'Customer Managed Key' (CMK)",
    '8.5 disknetworkaccess.py': "8.5 Ensure that 'Disk Network Access' is NOT set to 'Enable public access from all networks'",
    '8.6 dataaccessauth.py': "8.6 Ensure that 'Enable Data Access Authentication Mode' is 'Checked'",
    '8.7 approvedextensions.py': "8.7 Ensure that Only Approved Extensions Are Installed",
    '8.8 endpointprotection.py': "8.8 Ensure that Endpoint Protection for all Virtual Machines is installed",
    '8.11 trustedlaunch.py': "8.11 Ensure Trusted Launch is enabled on Virtual Machines",
    '9.1 httpsonly.py': "9.1 Ensure 'HTTPS Only' is set to On",
    '9.2 appserviceauth.py': "9.2 Ensure App Service Authentication is set up for apps in Azure App Service",
    '9.3 ftpsstate.py': "9.3 Ensure 'FTP State' is set to 'FTPS Only' or 'Disabled'",
    '9.4 webapptls.py': "9.4 Ensure Web App is using the latest version of TLS encryption",
    '9.5 registerwithentraid.py': "9.5 Ensure that Register with Entra ID is enabled on App Service",
    '9.6 webappbasicauth.py': "9.6 Ensure that 'Basic Authentication' is 'Disabled'",
    '9.7 phpversion.py': "9.7 Ensure that 'PHP version' is currently supported (if in use)",
    '9.8 pythonversion.py': "9.8 Ensure that 'Python version' is currently supported (if in use)",
    '9.9 javaversion.py': "9.9 Ensure that 'Java version' is currently supported (if in use)",
    '9.10 https20.py': "9.10 Ensure that 'HTTP20enabled' is set to 'true' (if in use)",
    '9.12 remotedebugging.py': "9.12 Ensure that 'Remote debugging' is set to 'Off'",
}


results = {}
timeout_seconds = 60
tmux_session_name = "persistent_powershell"


ANSI_HTML_MAPPING = {
    r'\x1b\[31m': '<span style="color:red;">',    
    r'\x1b\[32m': '<span style="color:green;">',  
    r'\x1b\[33m': '<span style="color:orange;">', 
    r'\x1b\[34m': '<span style="color:blue;">',   
    r'\x1b\[36m': '<span style="color:cyan;">',   
    r'\x1b\[37m': '<span style="color:white;">',  
    r'\x1b\[92m': '<span style="color:green;">',  
    r'\x1b\[91m': '<span style="color:red;">',    
    r'\x1b\[93m': '<span style="color:yellow;">', 
    r'\x1b\[94m': '<span style="color:blue;">',   
    r'\x1b\[96m': '<span style="color:cyan;">',   
    r'\x1b\[95m': '<span style="color:magenta;">',
    r'\x1b\[42m': '<span style="background-color:green;">',
    r'\x1b\[0m': '</span>',                       
}

def ansi_to_html(text):
    """Convert ANSI escape codes to HTML."""
    for ansi_code, html_tag in ANSI_HTML_MAPPING.items():
        text = re.sub(ansi_code, html_tag, text)
    while '<span' in text and text.count('<span') > text.count('</span>'):
        text += '</span>'
    return text

def start_tmux_powershell():
    """Start a new tmux session running PowerShell."""
    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", tmux_session_name, "pwsh"],
            check=True
        )
        print(f"{Fore.GREEN}Tmux session '{tmux_session_name}' started successfully.{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to start tmux session: {e}{Style.RESET_ALL}")
        sys.exit(1)

def send_command_to_tmux(command):
    """Send a command to the persistent PowerShell tmux session."""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", tmux_session_name, command, "C-m"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to send command to tmux session: {e}{Style.RESET_ALL}")
        sys.exit(1)

def authenticate_to_mggraph():
    """Authenticate to Microsoft Graph in the persistent PowerShell session."""
    print("\nAuthenticating to Microsoft Graph...\n")
    try:
        send_command_to_tmux("Import-Module Microsoft.Graph.Identity.SignIns")
        send_command_to_tmux("Connect-MgGraph")
    except Exception as e:
        print(f"{Fore.RED}Failed to authenticate: {e}{Style.RESET_ALL}")
        sys.exit(1)


def extract_final_status(output):
    """
    Extract the final status from the script output, handling HTML and edge cases.
    """
    
    soup = BeautifulSoup(output, "html.parser")
    clean_output = soup.get_text(separator=" ")

    
    match = re.search(r'final status:\s*(pass|fail|manual)', clean_output, re.IGNORECASE)
    if match:
        return match.group(1).strip().upper()

    
    if "enabled (secure transfer required)" in clean_output.lower():
        return "PASS"
    elif "error" in clean_output.lower() or "failed" in clean_output.lower():
        return "FAIL"
    elif "manual check required" in clean_output.lower():
        return "MANUAL"

    
    return "FAIL"


def run_script(script_name):
    """Run a script and determine its Final Status accurately."""
    description = script_descriptions.get(script_name, f"Running script: {script_name}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}\n{'*' * 60}\n{description.upper()}\n{'*' * 60}{Style.RESET_ALL}\n")

    try:
        master_fd, slave_fd = pty.openpty()

        process = subprocess.Popen(
            ['python3', script_name],
            stdout=slave_fd,
            stderr=slave_fd,
            text=True
        )

        os.close(slave_fd)

        output_lines = []
        start_time = datetime.now()
        last_output_time = start_time

        while True:
            if process.poll() is not None:  
                break

            if (datetime.now() - last_output_time).total_seconds() >= timeout_seconds:
                process.kill()
                os.close(master_fd)
                print(f"{Fore.RED}Script {script_name} timed out after {timeout_seconds} seconds of no output.{Style.RESET_ALL}")
                results[script_name] = {"Output": "Script timed out due to no output.", "Final Status": "SKIPPED"}
                return

            try:
                output = os.read(master_fd, 1024).decode()
                if output:
                    last_output_time = datetime.now()
                    sys.stdout.write(output)
                    sys.stdout.flush()
                    output_lines.append(output)
            except OSError:
                break

        while True:
            try:
                output = os.read(master_fd, 1024).decode()
                if not output:
                    break
                sys.stdout.write(output)
                sys.stdout.flush()
                output_lines.append(output)
            except OSError:
                break

        process.wait()
        full_output = ''.join(output_lines)

        
        final_status = extract_final_status(full_output)

        results[script_name] = {
            "Output": ansi_to_html(full_output),
            "Final Status": final_status,
            "Timestamp": datetime.now().isoformat()
        }

        os.close(master_fd)

    except Exception as ex:
        print(f"{Fore.RED}Unhandled exception for {script_name}: {ex}{Style.RESET_ALL}")
        results[script_name] = {
            "Output": str(ex),
            "Final Status": "FAIL",
            "Timestamp": datetime.now().isoformat()
        }

    except Exception as ex:
        print(f"{Fore.RED}Unhandled exception for {script_name}: {ex}{Style.RESET_ALL}")
        results[script_name] = {
            "Output": str(ex),
            "Final Status": "FAIL",
            "Timestamp": datetime.now().isoformat()
        }




def retry_skipped_scripts():
    """Retry scripts that were skipped due to timeout."""
    print("\nRetrying skipped scripts...\n")
    for script, result in results.items():
        if result["Final Status"] == "SKIPPED":
            print(f"Retrying {script}...")
            run_script(script)




def generate_html_report(results):
    """Generate an HTML report that dynamically validates the Final Status."""
    html_content = """
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Fira Code', monospace;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
                overflow-y: auto; /* Enable vertical scrolling */
            }
            details { 
                border: 1px solid #aaa; 
                border-radius: 4px; 
                margin: 0.5em 0; 
                padding: 0.5em;
                background-color: #fff;
            }
            details > summary { 
                font-weight: bold; 
                cursor: pointer; 
                background-color: #f9f9f9; 
                padding: 0.5em;
            }
            details > summary:hover { 
                background-color: #eaeaea; 
            }
            .fail { color: red; }
            .pass { color: green; }
            .manual { color: orange; }
            details[open] pre {
                background-color: #23252e; 
                white-space: pre-wrap; 
                word-wrap: break-word; 
                font-family: 'Fira Code', monospace;
                font-size: 15px;
                color: white; 
                margin: 0;
                padding: 0.5em; 
                max-height: 600px; 
                overflow: auto; /* Scrollable content inside details */
            }
            pre { 
                white-space: pre-wrap; 
                word-wrap: break-word; 
                font-family: 'Fira Code', monospace;
                margin: 0;
                padding: 0.5em;
                background-color: #f7f7f9;
                border-radius: 4px;
            }
            html, body {
                height: 100%; /* Ensure body takes up full height */
            }
        </style>
    </head>
    <body>
    """
    
    for script, result in results.items():
        output = result.get("Output", "")

        output_lower = output.lower()
        if "manual check required" in output_lower:
            final_status = "MANUAL"
            status_class = "manual"
        elif "final status: pass" in output_lower:
            final_status = "PASS"
            status_class = "pass"
        elif "final status: fail" in output_lower:
            final_status = "FAIL"
            status_class = "fail"
        else:
            final_status = "FAIL"
            status_class = "fail"

        result["Final Status"] = final_status

        description = script_descriptions.get(script, script)  

        html_content += f"""
        <details>
            <summary class="{status_class}">
                <strong>{description}:</strong> {final_status}
            </summary>
            <pre>{output}</pre>
        </details>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    html_file = f"results_{timestamp}.html"
    
    with open(html_file, "w") as f:
        f.write(html_content)
    
    print(f"HTML report generated: {html_file}")
    return html_file


def write_results_to_file(results, file_name="results.json"):
    """Write results to a JSON file."""
    try:
        with open(file_name, "w") as f:
            json.dump(results, f, indent=4)
        print(f"Results written to {file_name}")
    except Exception as e:
        print(f"Error writing results to file: {e}")



def capture_screenshot(html_file, output_directory):
    """Capture screenshots of only the failed results inside each dropdown."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    file_url = f"file://{os.path.abspath(html_file)}"
    driver.get(file_url)

    details_elements = driver.find_elements(By.TAG_NAME, "details")
    for element in details_elements:
        driver.execute_script("arguments[0].setAttribute('open', '')", element)

    for idx, element in enumerate(details_elements):
        try:
            summary_element = element.find_element(By.TAG_NAME, "summary")
            script_name = summary_element.text.split(":")[0].strip()
            sanitized_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in script_name)

            if "FAIL" in summary_element.text.upper():
                pre_element = element.find_element(By.TAG_NAME, "pre")
                driver.execute_script("arguments[0].scrollIntoView(true);", pre_element)

                screenshot_path = os.path.join(output_directory, f"{sanitized_name}.png")
                pre_element.screenshot(screenshot_path)
        except Exception as e:
            print(f"Failed to capture screenshot for script: {e}")

    driver.quit()






def run_single_script(script_name):
    """Run a specific script by its name."""
    if os.path.isfile(script_name):
        run_script(script_name)
    else:
        print(f"{Fore.RED}Script {script_name} not found. Please provide a valid script name.{Style.RESET_ALL}")




def main():
    parser = argparse.ArgumentParser(description="Run Azure scripts with optional single-script execution.")
    parser.add_argument(
        '--script',
        type=str,
        help="Specify a script to run by its name (e.g., '2.2.1 trusted locations.py')."
    )
    args = parser.parse_args()

    if args.script:
        if os.path.isfile(args.script):
            run_script(args.script)
        else:
            print(f"{Fore.RED}Script {args.script} not found. Please provide a valid script name.{Style.RESET_ALL}")
            return
    else:
        start_tmux_powershell()
        authenticate_to_mggraph()

        for script in scripts:
            if os.path.isfile(script):
                run_script(script)
            else:
                print(f"Script {script} not found. Skipping.")

        retry_skipped_scripts()

    html_file = generate_html_report(results)

    screenshot_dir = "screenshots"
    capture_screenshot(html_file, screenshot_dir)
    print("Screenshots Captured")

    write_results_to_file(results)

    subprocess.run(["tmux", "kill-session", "-t", "persistent_powershell"], check=True)

if __name__ == "__main__":
    main()

