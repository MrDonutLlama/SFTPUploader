# SFTP Uploader with File Hash Comparison

## Project Description

This Python script is designed to facilitate the secure and efficient uploading of files and directories to an SFTP server. The script ensures that files are only uploaded if they are new or have been modified, based on a comparison of file hash values between the local and remote directories. This approach reduces unnecessary data transfer and maintains the integrity of files on the remote server.

## Key Features

- **Recursive Directory Upload**: Upload all files and directories within a specified local directory to a corresponding directory on the SFTP server, preserving the directory structure.
- **File Hash Comparison**: Optionally computes and compares SHA-256 hash values of files to determine if they are identical or different, allowing for precise control over which files are replaced.
  - **Optional Hash Checking**: Users can choose whether or not to perform file hash comparisons. Skipping hash checks can significantly speed up the process, especially when dealing with large numbers of files.
- **Customizable Handling of Duplicates**:
  - Replace all files with different hashes.
  - Skip all files with different hashes.
  - Prompt for each file to decide whether to replace or skip.
- **Automatic Directory Creation**: Automatically creates directories on the remote server as needed, mirroring the local directory structure.
- **Progress Bars**: Utilizes TQDM to display progress bars, providing a visual indication of the upload process.
- **Color-Coded Output**: Provides clear, color-coded output to guide the user through the upload process and indicate actions taken.

## Configuration

The script requires configuration files to specify SFTP connection details. These configuration files are stored in a designated folder and allow the user to select different server configurations at runtime.

## Usage

The script is executed via the command line, where the user specifies the local directory to upload. The script then prompts the user to select a configuration file, choose how to handle files that differ based on their hash values, and decide whether or not to perform hash checks.

### Example Command

`python SFTPUploader.py "C:\path\to\local\directory"`

## Technologies Used

- **Python 3.6+**
- **paramiko**: For handling SFTP connections.
- **colorama**: For enhancing terminal output with colors.
- **TQDM**: For displaying progress bars during the upload process.

## Installation Instructions

Ensure you have Python 3.6 or higher installed. The script requires the installation of the following libraries:

`pip install paramiko colorama tqdm`

## License

This project is licensed under the MIT License.

