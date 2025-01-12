# Custom ISO Build with Kickstart

## Description

This script automates the process of creating a custom ISO image with a Kickstart configuration for automated installations.

## Requirements

- ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54&style=flat)

## Prerequisites

- The script must be run as root.
- The source ISO file must be available.
- Ensure the required packages are installed:
  - `mkisofs`
  - `rsync`
  - `sed`

## Installation

1. Clone the repository or download the script:
    ```bash
    git clone https://github.com/your-repo/Custom-ISO-build-with-Kickstart.git
    cd Custom-ISO-build-with-Kickstart
    ```

## Installation

1. Clone the repository or download the script:
    ```bash
    git clone https://github.com/your-repo/Custom-ISO-build-with-Kickstart.git
    cd Custom-ISO-build-with-Kickstart
    ```

2. Install required packages:
    ```bash
    sudo apt-get install mkisofs rsync sed  # For Debian-based systems
    sudo yum install mkisofs rsync sed      # For RedHat-based systems
    ```

## Usage

1. Make the script executable:
    ```bash
    chmod +x kickstart_iso_creator.py
    ```

2. Run the script:
    ```bash
    sudo ./kickstart_iso_creator.py
    ```

3. Follow the on-screen instructions to provide the path to the source ISO file.

4. The script will mount the ISO, extract its contents, and modify the boot parameters to include the Kickstart configuration.

5. Once the process is complete, the custom ISO will be created in the specified directory.

## Troubleshooting

- **Permission Denied**: Ensure you are running the script as root.
- **Missing Packages**: Install the required packages using the installation commands provided above.
- **ISO File Not Found**: Verify the path to the source ISO file.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
