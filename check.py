#!/usr/bin/env python3

import logging
import os
import pathlib
import subprocess
import json


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


logger = logging.getLogger(__name__)


def load_metadata(metadata_file):
    try:
        with open(metadata_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error("Error: File %s not found", metadata_file)
        exit(1)
    except json.JSONDecodeError as error_msg:
        logger.error("Error: Failed to parse json in %s: %s", metadata_file, error_msg)
        exit(1)

def write_inventory(metadata, hostname, inventory_target="/etc/ansible-init/inventory/inventory.ini"):
    groups = metadata.get("groups", [])
    inventory_content = ""
    for group in groups:
        group_name = group.get("name")
        if group_name:
            inventory_content += f"[{group_name}]\n{hostname}\n\n"

    inventory_file = inventory_target
    try:
        with open(inventory_file, "w") as file:
            file.write(inventory_content)
        logger.info("Inventory file %s created successfully!", inventory_file)
    except Exception as error_msg:
        logger.error("Error: Failed to write to %s: %s", inventory_file, error_msg)

def ansible_exec(cmd, *args, **kwargs):
    environ = os.environ.copy()
    environ["ANSIBLE_CONFIG"] = "/etc/ansible-init/ansible.cfg"
    cmd = f"/usr/bin/ansible-{cmd}"
    subprocess.run([cmd, *args], env=environ, check=True, **kwargs)

def mount_metadata(label="config-2"):
    environ = os.environ.copy()
    cmd = ["mount", f"/dev/disk/by-label/{label}", "/mnt"]
    subprocess.run(cmd, env=environ, check=True)


mount_metadata()
metadata_dir = "/mnt/openstack/latest/meta_data.json"
logger.info("fetching metadata from %s", metadata_dir)
metadata = load_metadata(metadata_dir)

logger.info("fetching hostname")
hostname = os.uname()[1]
logger.info("got hostname %s", hostname)

logger.info("starting to write inventory file")
write_inventory(metadata, hostname)

logger.info("executing /etc/ansible-init/playbooks/default.yml")
ansible_exec(
    "playbook", "--limit", hostname, "--connection", "local", "--inventory",
    "/etc/ansible-init/inventory/inventory.ini", "/etc/ansible-init/playbooks/default.yml"
)

logger.info("writing sentinel file /var/lib/ansible-init.done")
SENTINEL = pathlib.Path("/var/lib/ansible-init.done")
SENTINEL.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
SENTINEL.touch(mode=0o644)


logger.info("ansible-init completed successfully")
