import os
import paramiko
from scp import SCPClient, SCPException
from scp_config import HOSTNAME, USERNAME, PASSWORD, LOCAL_PATH, REMOTE_PATH, MATCH_STRING




def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File '{file_path}' has been deleted successfully.")
    except FileNotFoundError:
        print(f"The file '{file_path}' does not exist.")
    except PermissionError:
        print(f"Permission denied: unable to delete '{file_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_files(file_paths):
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
    
    for file_path in file_paths:
        try:
            os.remove(file_path)
            print(f"File '{file_path}' has been deleted successfully.")
        except FileNotFoundError:
            print(f"The file '{file_path}' does not exist.")
        except PermissionError:
            print(f"Permission denied: unable to delete '{file_path}'.")
        except Exception as e:
            print(f"An error occurred: {e}")

class SSHManager:
    """
    usage:
        >>> import SSHManager
        >>> ssh_manager = SSHManager()
        >>> ssh_manager.create_ssh_client(hostname, username, password)
        >>> ssh_manager.send_command("ls -al")
        >>> ssh_manager.send_file("/path/to/local_path", "/path/to/remote_path")
        >>> ssh_manager.get_file("/path/to/remote_path", "/path/to/local_path")
        ...
        >>> ssh_manager.close_ssh_client()
    """
    def __init__(self):
        self.ssh_client = None

    def create_ssh_client(self, hostname, username, password):
        """Create SSH client session to remote server"""
        if self.ssh_client is None:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(hostname, port=50032, username=username, password=password, look_for_keys=False)
        else:
            print("SSH client session exist.")

    def close_ssh_client(self):
        """Close SSH client session"""
        self.ssh_client.close()

    def send_file(self, local_path, remote_path, match_file_string):
        """Send a single file to remote path"""
        file_list = os.listdir(local_path)
        file_name = ""
        for i in file_list : 
            if match_file_string in i :
                file_name = i
                break
        if not file_name:
            print("There are no matching files!")
            exit(0)
        local_file_path = f"{local_path}/{file_name}"
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.put(local_file_path, remote_path, preserve_times=True)
        except SCPException:
            raise SCPException.message
        
        return local_file_path


    def send_files(self, local_path, remote_path, match_file_strings):
        """Send multiple files to remote path based on multiple match strings"""
        if not isinstance(match_file_strings, list):
            match_file_strings = [match_file_strings]
        
        file_list = os.listdir(local_path)
        matching_files = []
        
        for match_string in match_file_strings:
            matching_files.extend([f for f in file_list if match_string in f])
        
        if not matching_files:
            print("There are no matching files!")
            exit(0)
        
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                for file_name in matching_files:
                    local_file_path = f"{local_path}/{file_name}"
                    scp.put(local_file_path, remote_path, preserve_times=True)
        except SCPException as e:
            print(f"SCPException: {str(e)}")
            raise SCPException(str(e))
        
        return matching_files


    def get_file(self, remote_path, local_path):
        """Get a single file from remote path"""
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(remote_path, local_path)
        except SCPException:
            raise SCPException.message

    def send_command(self, command):
        """Send a single command"""
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        return stdout.readlines()

def send_file_to_remote(matchstring=None) :
    ssh_manager = SSHManager()
    ssh_manager.create_ssh_client(HOSTNAME, USERNAME, PASSWORD) 
    matchstr = matchstring if not None else MATCH_STRING
    local_file_path = ssh_manager.send_files(LOCAL_PATH, REMOTE_PATH, matchstr)
    delete_files(local_file_path)
    ssh_manager.close_ssh_client() 
