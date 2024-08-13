import os
import stat
import hashlib
import paramiko
import argparse
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def read_config(file_path):
    """Read the SFTP configuration from a text file."""
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
    return config

def list_remote_files(sftp, remote_path, compare_hashes):
    """List all files in the remote directory recursively and store their paths and hashes if required."""
    remote_files = {}
    try:
        for entry in sftp.listdir_attr(remote_path):
            remote_file_path = os.path.join(remote_path, entry.filename).replace("\\", "/")
            if stat.S_ISDIR(entry.st_mode):
                remote_files.update(list_remote_files(sftp, remote_file_path, compare_hashes))
            else:
                if compare_hashes:
                    print(f"{Fore.BLUE}Calculating hash for remote file: {remote_file_path}")
                    remote_files[remote_file_path] = {
                        "path": remote_file_path,
                        "hash": get_remote_file_hash(sftp, remote_file_path)
                    }
                else:
                    remote_files[remote_file_path] = {
                        "path": remote_file_path
                    }
    except FileNotFoundError:
        print(f"{Fore.RED}Remote path does not exist: {remote_path}")
    return remote_files

def get_file_hash(file_path):
    """Calculate the SHA-256 hash of a local file."""
    sha256 = hashlib.sha256()
    print(f"{Fore.BLUE}Calculating hash for local file: {file_path}")
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_remote_file_hash(sftp, remote_path):
    """Calculate the SHA-256 hash of a remote file."""
    sha256 = hashlib.sha256()
    with sftp.file(remote_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def ensure_remote_dir_exists(sftp, remote_dir):
    """Ensure that a remote directory exists, creating it if necessary."""
    dirs = []
    while len(remote_dir) > 1:
        dirs.append(remote_dir)
        remote_dir, _ = os.path.split(remote_dir)
    if len(remote_dir) == 1 and not remote_dir.startswith('/'):
        dirs.append(remote_dir)  # For a remote path like 'folder' (without a leading /)
    while dirs:
        remote_dir = dirs.pop().replace("\\", "/")  # Normalize path to use forward slashes
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            sftp.mkdir(remote_dir)
            print(f"{Fore.CYAN}Created directory: {remote_dir}")
        except Exception as e:
            print(f"{Fore.RED}Failed to create directory {remote_dir}: {e}")

def upload_files_sftp(sftp, local_path, remote_path, remote_files, counters, root_local_path, compare_hashes, replace_policy):
    """Upload files and directories recursively to an SFTP server, handling differences."""
    try:
        if os.path.isfile(local_path):
            relative_path = os.path.relpath(local_path, root_local_path)
            remote_file_path = os.path.join(remote_path, relative_path).replace("\\", "/")

            # Ensure the directory exists on the remote server
            remote_dir = os.path.dirname(remote_file_path)
            ensure_remote_dir_exists(sftp, remote_dir)

            remote_file_info = remote_files.get(remote_file_path)

            if remote_file_info:
                if compare_hashes:
                    local_hash = get_file_hash(local_path)
                    remote_hash = remote_file_info.get("hash")
                    if remote_hash and local_hash == remote_hash:
                        print(f"{Fore.YELLOW}Hashes match. Skipping file: {local_path}")
                        counters['skipped'] += 1
                    else:
                        print(f"{Fore.RED}Hashes differ. Handling file: {local_path}")
                        action = determine_action_for_different_file(local_path, replace_policy)
                        if action == "replace":
                            replace_file(sftp, local_path, remote_file_path, counters)
                        else:
                            print(f"{Fore.YELLOW}Skipped different file: {local_path}")
                            counters['skipped'] += 1
                else:
                    print(f"{Fore.YELLOW}Duplicate file found. Skipping file: {local_path}")
                    counters['skipped'] += 1
            else:
                print(f"{Fore.GREEN}Uploading new file: {local_path}")
                replace_file(sftp, local_path, remote_file_path, counters)

        elif os.path.isdir(local_path):
            for item in os.listdir(local_path):
                local_item_path = os.path.join(local_path, item)
                upload_files_sftp(sftp, local_item_path, remote_path, remote_files, counters, root_local_path, compare_hashes, replace_policy)
    except FileNotFoundError as e:
        print(f"{Fore.RED}File not found: {local_path} or {remote_file_path}. Error: {e}")
    except Exception as e:
        print(f"{Fore.RED}An error occurred during file upload: {e}")

def replace_file(sftp, local_path, remote_file_path, counters):
    """Replace the file on the remote server with the local file."""
    file_size = os.path.getsize(local_path)
    print(f"{Fore.MAGENTA}Starting upload: {local_path} -> {remote_file_path}")
    sftp.put(local_path, remote_file_path)
    print(f"{Fore.GREEN}Completed upload: {local_path}")
    counters['uploaded'] += 1
    counters['total_size'] += file_size

def determine_action_for_different_file(local_path, replace_policy):
    """Determine the action to take for a file that is different between local and remote."""
    if replace_policy == "replace_all":
        return "replace"
    elif replace_policy == "skip_all":
        return "skip"
    else:  # Ask for each file
        while True:
            response = input(f"{Fore.YELLOW}File '{local_path}' is different. Replace? (y/n): {Style.RESET_ALL}").strip().lower()
            if response == 'y':
                return "replace"
            elif response == 'n':
                return "skip"

def connect_and_upload(config, local_path, compare_hashes, replace_policy=None):
    """Establish SFTP connection and upload files."""
    sftp = None  # Initialize sftp variable
    try:
        # Check for all necessary keys in the config
        required_keys = ['host', 'port', 'username', 'password', 'remote_path']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")

        transport = paramiko.Transport((config['host'], int(config['port'])))
        transport.connect(username=config['username'], password=config['password'])

        sftp = paramiko.SFTPClient.from_transport(transport)
        print(f"{Fore.BLUE}Connected to SFTP server.")

        # Get the base folder name from the local path
        local_base_folder = os.path.basename(os.path.normpath(local_path))

        # Create a new directory in the remote path with the local folder's name
        remote_base_folder = os.path.join(config['remote_path'], local_base_folder).replace("\\", "/")
        ensure_remote_dir_exists(sftp, remote_base_folder)

        remote_files = list_remote_files(sftp, remote_base_folder, compare_hashes)

        counters = {'uploaded': 0, 'skipped': 0, 'total_size': 0}

        upload_files_sftp(sftp, local_path, remote_base_folder, remote_files, counters, local_path, compare_hashes, replace_policy)

        print(f"\n{Style.BRIGHT}Upload Summary:")
        print(f"{Fore.GREEN}Total files uploaded: {counters['uploaded']}")
        print(f"{Fore.YELLOW}Total files skipped: {counters['skipped']}")
        print(f"{Fore.CYAN}Total size transferred: {counters['total_size'] / (1024 * 1024):.2f} MB")

    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}")
    finally:
        if sftp is not None:
            sftp.close()
            print(f"{Fore.BLUE}SFTP connection closed.")

def choose_config(config_folder):
    """Display available config files and let the user choose one."""
    config_files = [f for f in os.listdir(config_folder) if f.endswith('.txt')]
    if not config_files:
        print(f"{Fore.RED}No configuration files found in the Config folder.")
        return None

    print(f"{Style.BRIGHT}Available configuration files:")
    for i, file_name in enumerate(config_files, start=1):
        display_name = os.path.splitext(file_name)[0]
        print(f"{Fore.CYAN}{i}. {display_name}")

    while True:
        try:
            choice = int(input(f"{Style.BRIGHT}Enter the number of the configuration file to use: "))
            if 1 <= choice <= len(config_files):
                selected_file = config_files[choice - 1]
                return os.path.join(config_folder, selected_file)
            else:
                print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(config_files)}.")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.")

def choose_compare_hashes():
    """Prompt the user to choose whether to compare hashes or not."""
    print(f"{Style.BRIGHT}\nWould you like to compare file hashes before uploading?")
    print(f"{Fore.GREEN}1. Yes, compare file hashes")
    print(f"{Fore.YELLOW}2. No, upload files without comparing hashes")
    
    while True:
        try:
            choice = int(input(f"{Style.BRIGHT}Enter your choice (1/2): {Style.RESET_ALL}"))
            if choice == 1:
                return True
            elif choice == 2:
                return False
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 1 or 2.")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter 1 or 2.")

def choose_replace_policy():
    """Prompt the user to choose a replace policy for handling different files."""
    print(f"{Style.BRIGHT}\nHow would you like to handle files with different hashes?")
    print(f"{Fore.GREEN}1. Replace all duplicate files with different hashes")
    print(f"{Fore.YELLOW}2. Skip all duplicate files with different hashes")
    print(f"{Fore.CYAN}3. Ask for each duplicate file with a different hash")
    
    while True:
        try:
            choice = int(input(f"{Style.BRIGHT}Enter your choice (1/2/3): {Style.RESET_ALL}"))
            if choice == 1:
                return "replace_all"
            elif choice == 2:
                return "skip_all"
            elif choice == 3:
                return "ask_each"
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload files to an SFTP server, avoiding duplicates.")
    parser.add_argument("local_path", help="Path to the local file or directory to upload")
    parser.add_argument("--config_folder", default="./Config", help="Path to the folder containing config files (default: ./Config)")
    args = parser.parse_args()

    config_file_path = choose_config(args.config_folder)
    if not config_file_path:
        exit(1)

    config = read_config(config_file_path)

    compare_hashes = choose_compare_hashes()

    if compare_hashes:
        replace_policy = choose_replace_policy()
    else:
        replace_policy = None

    connect_and_upload(config, args.local_path, compare_hashes, replace_policy)
