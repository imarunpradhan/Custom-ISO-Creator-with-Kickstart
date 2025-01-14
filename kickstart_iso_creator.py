#!/usr/bin/env python3
# Custom ISO Build with Kickstart

import os
import subprocess
import shutil
import logging
import argparse
from contextlib import contextmanager

# Constants
CONFIG = {
    "CWD": "./",
    "KICKSTART_CFG": "ks.cfg",
    "ISO_MOUNT": "mount",
    "ISO_EXTRACT": "extract",
    "KICKSTART_ISO_NAME": "Kickstart-",
    "ISO_LABEL_CMD": "echo | grep -oP 'LABEL=+\K[^ ]+' "
}
REQUIRED_PACKAGES = ["mkisofs", "rsync", "isomd5sum", "syslinux"]

def configure_logging(level):
    """Configure logging settings."""
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def check_root():
    """Check if the script is run as root."""
    if os.geteuid() != 0:
        logging.error("This script must be run as root.")
        exit(1)

def verify_os():
    """Verify if the operating system is supported."""
    try:
        with open("/etc/os-release") as distro:
            os_info = distro.read()
            if any(keyword in os_info for keyword in ["fedora", "centos", "rocky", "rhel", "ol"]):
                return
        logging.error("This script only supports Fedora, CentOS, Rocky Linux, RHEL, and Oracle Linux.")
        exit(1)
    except FileNotFoundError:
        logging.error("/etc/os-release file not found.")
        exit(1)

def manage_directory(directory, create=True):
    """Create or clean up a directory."""
    if os.path.exists(directory):
        shutil.rmtree(directory)
    if create:
        os.makedirs(directory)

def execute_command(command, success_message):
    """Execute a shell command and log the success or failure."""
    try:
        subprocess.run(command, shell=True, check=True)
        logging.info(success_message)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}\n{e}")
        handle_error()

def get_iso_label():
    """Retrieve the ISO label from the extracted ISO files."""
    try:
        label = subprocess.check_output(CONFIG["ISO_LABEL_CMD"] + CONFIG["CWD"] + CONFIG["ISO_EXTRACT"] + "/isolinux/isolinux.cfg | head -1", shell=True)
        return label.decode().strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get ISO label: {e}")
        handle_error()

def modify_boot_parameters(label):
    """Modify the boot parameters in the extracted ISO files."""
    commands = [
        f"sed -i 's@append initrd=initrd.img inst.stage2=hd:LABEL={label} quiet@append initrd=initrd.img inst.text inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label}@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/isolinux/isolinux.cfg",
        f"sed -i 's@append initrd=initrd.img inst.stage2=hd:LABEL={label} rd.live.check quiet@append initrd=initrd.img inst.text inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label} rd.live.check@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/isolinux/isolinux.cfg",
        f"sed -i 's@Install@Kickstart Install@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/EFI/BOOT/grub.cfg",
        f"sed -i 's@1@0@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/EFI/BOOT/grub.cfg",
        f"sed -i 's@install@Kickstart Install Rocky Linux 9.0@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/EFI/BOOT/grub.cfg",
        f"sed -i 's@inst.stage2=hd:LABEL={label} quiet@inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label}@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/EFI/BOOT/grub.cfg",
        f"sed -i 's@inst.stage2=hd:LABEL={label} rd.live.check quiet@inst.ks=cdrom:/ks.cfg inst.stage2=hd:LABEL={label} rd.live.check@g' {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/EFI/BOOT/grub.cfg"
    ]
    for cmd in commands:
        execute_command(cmd, "Modifying boot parameters")

def check_and_install_packages():
    """Check and install required packages."""
    missing_packages = [pkg for pkg in REQUIRED_PACKAGES if shutil.which(pkg) is None]

    if missing_packages:
        logging.info(f"Missing packages: {', '.join(missing_packages)}. Attempting to install...")
        if os.path.exists("/etc/redhat-release"):
            execute_command(f"yum install {' '.join(missing_packages)} -y", "Installing missing packages")
        else:
            logging.error("Unsupported operating system for automatic package installation.")
            exit(1)

def create_kickstart_iso(label):
    """Create the Kickstart ISO."""
    iso_command = f"mkisofs -relaxed-filenames -J -R -o {CONFIG['CWD']}{CONFIG['KICKSTART_ISO_NAME']}{os.path.basename(SOURCE_ISO)} -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -V '{label}' -boot-load-size 4 -boot-info-table -eltorito-alt-boot -eltorito-platform efi -b images/efiboot.img -no-emul-boot {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}"
    execute_command(iso_command, "Creating Kickstart ISO")

def handle_error():
    """Handle errors gracefully and clean up."""
    manage_directory(CONFIG["CWD"] + CONFIG["ISO_MOUNT"], create=False)
    manage_directory(CONFIG["CWD"] + CONFIG["ISO_EXTRACT"], create=False)
    exit(1)

def validate_source_iso(source_iso):
    """Validate the presence of the source ISO file."""
    if not os.path.isfile(source_iso):
        logging.error("Source ISO file not exists.")
        handle_error()

@contextmanager
def mount_iso(source_iso, mount_point):
    """Context manager to mount and unmount the ISO."""
    execute_command(f"mount {source_iso} {mount_point}", "Mounting source ISO")
    try:
        yield
    finally:
        execute_command(f"umount {mount_point}", "Un-mounting source ISO")

def create_iso():
    """Create the custom ISO with Kickstart."""
    manage_directory(CONFIG["CWD"] + CONFIG["ISO_MOUNT"])
    manage_directory(CONFIG["CWD"] + CONFIG["ISO_EXTRACT"])
    with mount_iso(SOURCE_ISO, CONFIG["CWD"] + CONFIG["ISO_MOUNT"]):
        execute_command(f"rsync -a --info=progress2 --human-readable {CONFIG['CWD']}{CONFIG['ISO_MOUNT']}/ {CONFIG['CWD']}{CONFIG['ISO_EXTRACT']}/", "Extracting source ISO")
    shutil.copy(CONFIG["CWD"] + CONFIG["KICKSTART_CFG"], CONFIG["CWD"] + CONFIG["ISO_EXTRACT"])
    ISO_LABEL = get_iso_label()
    modify_boot_parameters(ISO_LABEL)
    if os.path.exists(CONFIG["CWD"] + CONFIG["KICKSTART_ISO_NAME"] + os.path.basename(SOURCE_ISO) + ".iso"):
        os.remove(CONFIG["CWD"] + CONFIG["KICKSTART_ISO_NAME"] + os.path.basename(SOURCE_ISO) + ".iso")
    create_kickstart_iso(ISO_LABEL)
    execute_command(f"sudo isohybrid --uefi {CONFIG['CWD']}{CONFIG['KICKSTART_ISO_NAME']}{os.path.basename(SOURCE_ISO)}", "Hybridizing ISO")
    execute_command(f"sudo implantisomd5 {CONFIG['CWD']}{CONFIG['KICKSTART_ISO_NAME']}{os.path.basename(SOURCE_ISO)}", "Embedding MD5 checksum")
    manage_directory(CONFIG["CWD"] + CONFIG["ISO_MOUNT"], create=False)
    manage_directory(CONFIG["CWD"] + CONFIG["ISO_EXTRACT"], create=False)

def main():
    """Main function to orchestrate the Kickstart ISO creation process."""
    parser = argparse.ArgumentParser(description="Create a custom ISO with Kickstart")
    parser.add_argument("source_iso", help="Path to the source ISO file")
    parser.add_argument("--log-level", default="WARNING", help="Set the logging level (default: WARNING)")
    args = parser.parse_args()

    global SOURCE_ISO
    SOURCE_ISO = args.source_iso

    configure_logging(args.log_level)

    try:
        check_root()
        verify_os()
        check_and_install_packages()
        validate_source_iso(SOURCE_ISO)
        create_iso()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        handle_error()

if __name__ == "__main__":
    main()
