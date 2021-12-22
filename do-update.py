#!/usr/bin/env python


import requests, sys, json, math, smtplib
# Import the email modules we'll need
from email.message import EmailMessage
from time import sleep
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Define part 
endpoint = 'https://<Vcenter adres>/api'
VCusername = '<Username>'
VCpassword = '<Password>'
VCUpdateSource = 'LOCAL_AND_ONLINE'


# Functions here

def AuthToApplMGMT():
    # Auth Section
    response = requests.post(endpoint+"/session", verify=False, auth=HTTPBasicAuth(VCusername, VCpassword))
    response_json = response.json()
    #print(response_json)
    Authtoken = response_json
    print("Login[{}]: {}".format(response.status_code ,response_json))
    return Authtoken

def GetUpdates(FuncToken): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    response = requests.get(endpoint+"/appliance/update/pending?source_type={}".format(VCUpdateSource), headers=headers, verify=False)
    response_json = response.json()
    #print(response_json) #Debug
    try:
        PatchVersion = response_json[0]['version']
    except KeyError:
        if response_json['error_type'] == 'NOT_FOUND':
            PatchVersion = "None"
        else:
            PatchVersion = "Error"

    print("GetUpdates[{}]: {}".format(response.status_code ,PatchVersion))

    return PatchVersion

def DoStage(FuncToken,FuncPatchVersion): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    response = requests.post(endpoint+"/appliance/update/pending/{}?action=stage".format(FuncPatchVersion), headers=headers, verify=False)
    #response_json = response.json()
    if response.status_code == 204:
        StageIs = "Succes"
    else:
        StageIs = "Failed"

    print("Staged[{}]: {}".format(response.status_code,StageIs ))

def DoValidate(FuncToken,FuncPatchVersion): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    Body = {
        "user_data": {}
    }
    response = requests.post(endpoint+"/appliance/update/pending/{}?action=validate".format(FuncPatchVersion), headers=headers, data=json.dumps(Body), verify=False)
    #response_json = response.json()
    print(json.dumps(Body))
    if response.status_code == 204:
        VerifyIs = "Succes"
    else:
        VerifyIs = "Failed"

    print("ValidateStarted[{}]: {}".format(response.status_code,VerifyIs ))

def DoInstall(FuncToken,FuncPatchVersion): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    Body = {
        "user_data": {}
    }
    response = requests.post(endpoint+"/appliance/update/pending/{}?action=install".format(FuncPatchVersion), headers=headers, data=json.dumps(Body), verify=False)
    #response_json = response.json()
    if response.status_code == 204:
        InstallIs = "Succes"
    else:
        InstallIs = "Failed"

    print("InstallStarted[{}]: {}".format(response.status_code,InstallIs ))


def GetStageStatus(FuncToken): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    WhileLoop=False
    #Do A While loop to check if staging is allowed
    while not WhileLoop:
        response = requests.get(endpoint+"/appliance/update/staged", headers=headers, verify=False)
        response_json = response.json()
        try:
            response_json['staging_complete']
            WhileLoop=True
        except KeyError:
            print("  StagedStatus[{}]: Not staging yet".format(response.status_code))
        #Wait a second not to spam vCenter
        sleep(1)
        
    #print(response_json) #Debug

    print("  StagedStatus[{}]: {}".format(response.status_code, response_json['staging_complete'] ))
    return response_json['staging_complete']

def GetPendingStatus(FuncToken,FuncPatchVersion): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    response = requests.get(endpoint+"/appliance/update/pending/{}".format(FuncPatchVersion), headers=headers, verify=False)
    response_json = response.json()
    #print(response_json) #Debug

    print("  PendingStatus-Staged[{}]: {}".format(response.status_code, response_json['staged'] ))
    return response_json['staged']

def GetUpdateStatus(FuncToken): 
    # DataUsage Section
    headers = {
        "vmware-api-session-id": FuncToken
    }
    response = requests.get(endpoint+"/appliance/update", headers=headers, verify=False)
    response_json = response.json()
    #print(response_json) #Debug

    try:
        Completed = response_json['task']['progress']['completed']
        DefaultMsg = response_json['task']['progress']['message']["default_message"]
        StatusMsg = response_json['task']["status"]
        print("  UpdateStatus[{}]: {}% working on {} {}".format(response.status_code, Completed, StatusMsg, DefaultMsg))
    except KeyError:
        sleep(0.1)

    return response_json['state']


def WaitForStaged(FuncToken): 
    #Wait for StageProgress
    AmIStaged=False
    while not AmIStaged:
        sleep(5)
        AmIStaged=GetStageStatus(FuncToken)

    print("IsStaged: {}".format(AmIStaged))

def WaitForUpdate(FuncToken): 
    #Wait for Update
    AmIUpdated=False
    while not AmIUpdated == "UP_TO_DATE":
        sleep(2)
        AmIUpdated=GetUpdateStatus(FuncToken)

    print("IsUpdated: {}".format(AmIUpdated))


def LogOffSession(FuncToken):
    #Logout
    headers = {"vmware-api-session-id": FuncToken}
    response = requests.delete(endpoint+"/session", headers=headers, verify=False)
    if response.status_code == 204:
        LogOff = "Succes"
    else:
        LogOff = "Failed"

    print("Logout: {}".format(LogOff))

def main():
    global Token
    Token = AuthToApplMGMT()
    PatchVersion = GetUpdates(Token)
    if PatchVersion == "None":
        print("No updates found!")
    elif PatchVersion == "Error":
        print("Error while searching for updates")
    else:
        DoStage(Token,PatchVersion)
        WaitForStaged(Token)
        #DoValidate(Token,PatchVersion) Werkt nog niet
        # May need Validate wait
        DoInstall(Token,PatchVersion)
        WaitForUpdate(Token)
    LogOffSession(Token)

# Start program
# Main program
if __name__ == '__main__':
    try:
        main()
        #print ListOfSwitchDiffs
    except KeyboardInterrupt:
        print ('\nChickend out')
        print ("          /')")
        print ("  ////  /' )'")
        print (" @   \/'  )'")
        print ("< (  (_...)'")
        print ("  \      )")
        print ("   \,,,,/")
        print ("     _|_        \n")

        LogOffSession(Token)
        sys.exit(0)
    except SystemExit:
        print ("Script exit, please try again")
        sys.exit(2)
