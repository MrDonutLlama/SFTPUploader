SFTP Uploader with File Hash Comparison
This Python script allows you to upload files and directories to an SFTP server, ensuring that files are only replaced if they differ based on their hash values. It gives you the flexibility to decide how to handle duplicate files that differ between the local and remote locations.

Features
Recursive Directory Upload: Uploads all files within a specified directory and its subdirectories to the SFTP server.
File Hash Comparison: Compares the hash of local files with those on the server to determine if they should be replaced.
Customizable Handling of Duplicates: Choose whether to replace all different files, skip them, or be prompted for each file.
Automatic Directory Creation: Automatically creates remote directories that do not exist, mirroring the structure of the local directory.
Color-Coded Output: Provides clear, color-coded prompts and messages to enhance the user experience.
Installation
Prerequisites
Python 3.6 or higher
Required Python packages:
paramiko for SFTP connections
colorama for color-coded terminal output
Installation Steps
Clone the Repository:

bash
Copy code
git clone https://github.com/your-username/sftp-uploader.git
cd sftp-uploader
Install Required Python Packages:

bash
Copy code
pip install paramiko colorama
Configuration
Creating Configuration Files
Before running the script, you need to create configuration files that contain the necessary SFTP connection details.

Create a Config Folder:
Create a folder named Config in the same directory as the script (or specify a different folder when running the script).

Create Configuration Files:
Inside the Config folder, create one or more text files (e.g., sftp_config1.txt, sftp_config2.txt) with the following content:

ini
Copy code
host=sftp.example.com
port=22
username=myusername
password=mypassword
remote_path=/remote/directory/path
Usage
Running the Script
Basic Command:
To run the script, specify the local directory you want to upload:

bash
Copy code
python SFTPUploader.py "C:\path\to\local\directory"
Select a Configuration:
The script will prompt you to choose from the available configuration files in the Config folder.

Choose How to Handle Duplicate Files with Different Hashes:
The script offers three options:

Option 1: Replace all duplicate files with different hashes.
Option 2: Skip all duplicate files with different hashes.
Option 3: Ask for each duplicate file with a different hash.
Example
bash
Copy code
$ python SFTPUploader.py "C:\Users\YourName\Documents\MyProject"
Available configuration files:
1. sftp_config1
2. sftp_config2
Enter the number of the configuration file to use: 1

How would you like to handle files with different hashes?
1. Replace all duplicate files with different hashes
2. Skip all duplicate files with different hashes
3. Ask for each duplicate file with a different hash
Enter your choice (1/2/3): 1

Connected to SFTP server.
Starting upload: C:\Users\YourName\Documents\MyProject\file1.txt -> /remote/directory/path/MyProject/file1.txt
Completed upload: C:\Users\YourName\Documents\MyProject\file1.txt
...
Upload Summary:
Total files uploaded: 5
Total files skipped: 3
Total size transferred: 14.25 MB
SFTP connection closed.
License
This project is licensed under the MIT License. See the LICENSE file for details.

Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss any changes or suggestions.