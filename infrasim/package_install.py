"""
*********************************************************
Copyright @ 2015 EMC Corporation All Rights Reserved
*********************************************************
"""

import requests
import os
import hashlib
from infrasim import run_command, CommandRunFailed

"""
this script is used to install the necessary packages before starting infrasim-compute
the packages includes:
    ipmitool libssh-dev libpython-dev libffi-dev libyaml-dev
    infrasim-qemu
    infrasim-openipmi
besides, seabios binary file is also downloaded into expected folder
"""


BASE_URL = "https://api.bintray.com/packages/infrasim/"


def install_official_packages():
    run_command("apt-get install -y socat ipmitool libssh-dev libffi-dev libyaml-dev")


def install_bintray_packages(repo, package):
    # get latest version number
    print("downloading " + package + "...")
    if package is "Infrasim_Qemu":
        infrasim_version = "1.0"
    elif package is "OpenIpmi":
        infrasim_version = "1.4"
    elif package is "Seabios":
        infrasim_version = "1.3"
    else:
        raise Exception("No {} package in {}".format(package, BASE_URL))
    download_link = BASE_URL + repo + "/" + package + "/versions/" \
                    + infrasim_version + "/files"
    print("downloading " + download_link + "...")
    response = requests.get(download_link)
    data = response.json()
    latest_time = data[0]["created"]
    path = ""
    file_name = ""
    sha256 = ""
    for item in data:
        if item["created"] >= latest_time:
            latest_time = item["created"]
            path = item["path"]
            file_name = item["name"]
            sha256 = item["sha256"]
    download_link = "https://dl.bintray.com/infrasim/" + repo + "/" + path
    print("downloading " + download_link + "...")
    response = requests.get(download_link)
    if not response:
        raise Exception("Failed to fetch package {} from bintray.\n"
                        "response code is {}".format(package, response))
    if not len(response.content):
        raise Exception("Failed to fetch package {} from bintray.\n"
                        "Length of file is zero.".format(package))
    if package is "Seabios":
        file_name = os.path.join("/usr/local/share/qemu/", "bios-256k.bin")
    else:
        file_name = "/tmp/" + file_name
    with open(file_name, "wb") as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)
    if hashlib.sha256(open(file_name, "rb").read()).hexdigest() != sha256:
        raise Exception(
            "The file {} downloaded is not complete, please try again!")
    if package is not "Seabios":
        print("installing {} {}...".format(package, infrasim_version))
        run_command("dpkg -i " + file_name)


def check_package(package="Qemu", cmd="which qemu-system-x86_64"):
    has_package = True
    # Check if package installed
    try:
        run_command(cmd)
    except CommandRunFailed:
        has_package = False

    # Confirm whether to install package
    install_package = True
    if has_package:
        while True:
            ans = raw_input(package + " already exists. Overwrite it? (Y/n)")
            if ans.lower() not in ('yes', 'no', 'y', 'n'):
                print("Invalid input. Please respond with 'yes' or 'no' (or 'y' or 'n').")
                continue
            else:
                break
        if ans.lower() in ('no', 'n'):
            install_package = False

    return has_package, install_package


def package_install():
    install_official_packages()

    has_qemu, install_qemu = check_package("Qemu", "which qemu-system-x86_64")
    has_openipmi, install_openipmi = check_package("Openipmi", "which ipmi_sim")
    has_seabios, install_seabios = check_package("Seabios", "ls /usr/local/share/qemu/bios-256k.bin")

    if install_qemu:
        if not has_qemu:
            install_bintray_packages("deb", "Infrasim_Qemu")
        elif not install_seabios:
            run_command("mv /usr/local/share/qemu/bios-256k.bin /usr/local/share/qemu/bios-256k.bin.bk")
            run_command("dpkg -r infrasim-qemu")
            install_bintray_packages("deb", "Infrasim_Qemu")
            run_command("mv /usr/local/share/qemu/bios-256k.bin.bk /usr/local/share/qemu/bios-256k.bin")
        else:
            run_command("dpkg -r infrasim-qemu")
            install_bintray_packages("deb", "Infrasim_Qemu")
    if install_openipmi:
        if has_openipmi:
            run_command("dpkg -r infrasim-openipmi")
        install_bintray_packages("deb", "OpenIpmi")
    if install_seabios:
        install_bintray_packages("generic", "Seabios")
