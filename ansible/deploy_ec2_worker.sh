#!/bin/bash
set -e

# The SSH credentials can be bootstrapped by specifying the ec2_worker_ssh_public_key env var in terraform cloud.
# Requires jq to be installed

# Get dynamic parameters from Terraform
tf_output="$(terraform -chdir=../terraform output -json)"

# Inventory can be passed directly as a CSV:
# https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#inventory-sources
# Adding a trailing comma ensures it is recognised as such
inventory="$(jq --raw-output '.ec2_worker_hostnames.value|join(",")' <<< "$tf_output"),"
echo "Running ansible on $inventory"

# extra_vars="$(jq '{django_vars: .all_django_vars.value}' <<< "$tf_output")"
# inject the location of the ssl certs on the worker
extra_vars=$(echo $(echo "$(jq '.all_django_vars.value' <<< "$tf_output")" '{"SSL_CERT_DIR": "/etc/ssl/certs"}' | jq -s add) | jq '{django_vars: .}')
echo "Django configuration:"
echo $extra_vars

# Download Ansible role
ansible-galaxy install \
  --force \
  --roles-path=./roles \
  girder.celery

# Install dependency for playbook
ansible-galaxy collection install \
  --force \
  ansible.posix

# Run Ansible playbook
export ANSIBLE_HOST_KEY_CHECKING=False
echo "Running playbook"
ansible-playbook \
  --inventory "$inventory" \
  --extra-vars "$extra_vars" \
  ./playbook.yml
