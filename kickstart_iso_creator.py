#!/usr/bin/env python3
# Custom ISO Build with Kickstart

import os
import subprocess
import importlib.util
import shutil
import logging

# Constants
CWD = "./"
KICKSTART_KS_CFG = "ks.cfg"
ISO_SOURCE_MOUNT = "mount"
ISO_SOURCE_EXTRACT = "extract"
KICKSTART_ISO_NAME = "Kickstart-"
ISO_LABEL_CMD = "echo | grep -oP 'LABEL=+\K[^ ]+' "

# Clear the terminal
os.system("clear")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assign color codes
WHITE = '\x1b[1;37;40m'
GREEN = '\x1b[1;32;40m'
BLUE = '\x1b[1;36;40m'
ORANGE = '\x1b[1;33;40m'
RED = '\x1b[1;31;40m'
RED_FLASHING = '\x1b[6;31;40m'

def check_root():
    """Check if the script is run as root."""
    if os.geteuid() != 0:
        logging.error("This script must be run as root.")
        exit(1)

def determine_os():
    """Determine the operating system and return the appropriate ISO package handler."""
    try:
        with open("/etc/os-release") as distro:
            for line in distro:
                if "centos" in line:
                    return "CentOS", "mkisofs"
                elif "fedora" in line:
                    return "Fedora", "mkisofs"
                elif "debian" in line:
                    return "Debian", "mkisofs"
                elif "kali" in line:
                    return "Kali", "mkisofs"
    except FileNotFoundError:
        logging.error("/etc/os-release file not found.")
    return "This OS is not supported", None

def check_and_create_dir(directory):
    """Check if a directory exists, and create it if it does not."""
    try:
        if os.path.exists(directory):
            logging.info(f"Removing existing {directory} directory")
            shutil.rmtree(directory)
        logging.info(f"Creating {directory} directory")
        os.makedirs(directory)
    except OSError as e:
        logging.error(f"Error creating directory {directory}: {e}")

def execute_command(command, success_message):
    """Execute a shell command and log the success or failure."""
    try:
        result = subprocess.run(command, shell=True, check=True)
        logging.info(success_message)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}\n{e}")
        handle_error()

def get_iso_label():
    """Retrieve the ISO label from the extracted ISO files."""
    try:
        label = subprocess.check_output(ISO_LABEL_CMD + CWD + ISO_SOURCE_EXTRACT + "/isolinux/isolinux.cfg | head -1", shell=True)
        return label.decode().strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get ISO label: {e}")
        handle_error()
        return ""

def modify_boot_parameters(label):
    """Modify the boot parameters in the extracted ISO files."""
    commands = [
        f"sed -i 's@append initrd=initrd.img inst.stage2=hd:LABEL={label} quiet@append initrd=initrd.img inst.text inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label}@g' {CWD}{ISO_SOURCE_EXTRACT}/isolinux/isolinux.cfg",
        f"sed -i 's@append initrd=initrd.img inst.stage2=hd:LABEL={label} rd.live.check quiet@append initrd=initrd.img inst.text inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label} rd.live.check@g' {CWD}{ISO_SOURCE_EXTRACT}/isolinux/isolinux.cfg",
        f"sed -i 's@Install@Kickstart Install@g' {CWD}{ISO_SOURCE_EXTRACT}/EFI/BOOT/grub.cfg",
        f"sed -i 's@1@0@g' {CWD}{ISO_SOURCE_EXTRACT}/EFI/BOOT/grub.cfg",
        f"sed -i 's@install@Kickstart Install Rocky Linux 9.0@g' {CWD}{ISO_SOURCE_EXTRACT}/EFI/BOOT/grub.cfg",
        f"sed -i 's@inst.stage2=hd:LABEL={label} quiet@inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label}@g' {CWD}{ISO_SOURCE_EXTRACT}/EFI/BOOT/grub.cfg",
        f"sed -i 's@inst.stage2=hd:LABEL={label} rd.live.check quiet@inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label} rd.live.check@g' {CWD}{ISO_SOURCE_EXTRACT}/EFI/BOOT/grub.cfg"
    ]
    for cmd in commands:
        execute_command(cmd, "Modifying boot parameters")

def install_package_if_missing(package, distro):
    """Install the required package if it is missing."""
    if importlib.util.find_spec(package) is None:
        logging.info("Checking for ISO package handler")
        install_command = f"yum install {package} -y" if distro in ["CentOS", "Fedora"] else f"apt install {package} -y"
        execute_command(install_command, f"Installing {package}")

def create_kickstart_iso(distro, package, label):
    """Create the Kickstart ISO."""
    install_package_if_missing(package, distro)
    logging.info("Creating Kickstart ISO")
    iso_command = f"{package} -relaxed-filenames -J -R -o {CWD}{KICKSTART_ISO_NAME}{os.path.basename(SOURCE_ISO_NAME)} -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -V '{label}' -boot-load-size 4 -boot-info-table -eltorito-alt-boot -eltorito-platform efi -b images/efiboot.img -no-emul-boot {CWD}{ISO_SOURCE_EXTRACT}"
    execute_command(iso_command, "Creating Kickstart ISO")

def clean_up():
    """Clean up temporary directories."""
    try:
        if os.path.exists(CWD + ISO_SOURCE_MOUNT):
            shutil.rmtree(CWD + ISO_SOURCE_MOUNT)
        if os.path.exists(CWD + ISO_SOURCE_EXTRACT):
            shutil.rmtree(CWD + ISO_SOURCE_EXTRACT)
    except OSError as e:
        logging.error(f"Error cleaning up directories: {e}")

def check_required_commands():
    """Check if all required commands are available."""
    required_commands = ["mount", "rsync", "sed", "isohybrid", "implantisomd5"]
    for cmd in required_commands:
        if shutil.which(cmd) is None:
            logging.error(f"Required command not found: {cmd}")
            exit(1)

def handle_error():
    """Handle errors gracefully and clean up."""
    logging.error("An error occurred. Cleaning up and exiting.")
    clean_up()
    exit(1)

def log_step_start(step_name):
    """Log the start of a step."""
    logging.info(f"Starting step: {step_name}")

def log_step_end(step_name):
    """Log the end of a step."""
    logging.info(f"Completed step: {step_name}")

def validate_source_iso(source_iso_name):
    """Validate the presence of the source ISO file."""
    if os.path.isfile(source_iso_name):
        logging.info("Source ISO file exists.")
    else:
        logging.error("Source ISO file not exists.")
        handle_error()

def log_process_start():
    """Log the start of the entire process."""
    logging.info("Starting the Kickstart ISO creation process")

def log_process_complete():
    """Log the completion of the entire process."""
    logging.info("Kickstart ISO complete. The ISO file is located in the current working directory")
    logging.info("** PROCESS COMPLETE **")

def log_process_end():
    """Log the end of the script."""
    logging.info("Script execution completed")

def log_script_initialization():
    """Log the initialization of the script."""
    logging.info("Initializing the Kickstart ISO creation script")

def main():
    """Main function to orchestrate the Kickstart ISO creation process."""
    global SOURCE_ISO_NAME
    SOURCE_ISO_NAME = input("Please provide the path to the source ISO file: ")

    try:
        log_script_initialization()
        log_process_start()
        check_root()
        check_required_commands()
        OS_DISTRO, ISOPACKAGE = determine_os()
        logging.info(f"Current Linux Distro: {OS_DISTRO}")

        log_step_start("Validate source ISO")
        validate_source_iso(SOURCE_ISO_NAME)
        log_step_end("Validate source ISO")

        log_step_start("Check and create directories")
        check_and_create_dir(CWD + ISO_SOURCE_MOUNT)
        check_and_create_dir(CWD + ISO_SOURCE_EXTRACT)
        log_step_end("Check and create directories")

        log_step_start("Mount source ISO")
        execute_command(f"mount {SOURCE_ISO_NAME} {CWD}{ISO_SOURCE_MOUNT}", "Mounting source ISO")
        log_step_end("Mount source ISO")

        log_step_start("Extract source ISO")
        execute_command(f"rsync -a --info=progress2 --human-readable {CWD}{ISO_SOURCE_MOUNT}/ {CWD}{ISO_SOURCE_EXTRACT}/", "Extracting source ISO")
        log_step_end("Extract source ISO")

        log_step_start("Copy kickstart config")
        try:
            shutil.copy(CWD + KICKSTART_KS_CFG, CWD + ISO_SOURCE_EXTRACT)
            logging.info("Copying kickstart config to extracted ISO")
        except IOError as e:
            logging.error(f"Error copying kickstart config: {e}")
            handle_error()
        log_step_end("Copy kickstart config")

        log_step_start("Get ISO label")
        ISO_LABEL = get_iso_label()
        logging.info(f"The current ISO label is {ISO_LABEL}")
        log_step_end("Get ISO label")

        log_step_start("Modify boot parameters")
        modify_boot_parameters(ISO_LABEL)
        log_step_end("Modify boot parameters")

        log_step_start("Create Kickstart ISO")
        if os.path.exists(CWD + KICKSTART_ISO_NAME + os.path.basename(SOURCE_ISO_NAME) + ".iso"):
            os.remove(CWD + KICKSTART_ISO_NAME + os.path.basename(SOURCE_ISO_NAME) + ".iso")
        create_kickstart_iso(OS_DISTRO, ISOPACKAGE, ISO_LABEL)
        log_step_end("Create Kickstart ISO")

        log_step_start("Unmount source ISO")
        execute_command(f"umount {CWD}{ISO_SOURCE_MOUNT}", "Un-mounting source ISO")
        log_step_end("Unmount source ISO")

        log_step_start("Hybridize and embed checksum")
        execute_command(f"sudo isohybrid --uefi {CWD}{KICKSTART_ISO_NAME}{os.path.basename(SOURCE_ISO_NAME)}", "Hybridizing ISO")
        execute_command(f"sudo implantisomd5 {CWD}{KICKSTART_ISO_NAME}{os.path.basename(SOURCE_ISO_NAME)}", "Embedding MD5 checksum")
        log_step_end("Hybridize and embed checksum")

        log_process_complete()

        clean_up()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        handle_error()
    finally:
        log_process_end()

if __name__ == "__main__":
    main()
