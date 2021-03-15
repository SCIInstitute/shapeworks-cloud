#!/bin/bash
set -e

# Get dynamic parameters from Terraform
tf_output="$(terraform output -json)"

# Inventory can be passed directly as a CSV:
# https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#inventory-sources
# Adding a trailing comma ensures it is recognised as such
inventory="$(jq --raw-output '.ec2_worker_hostnames.value|join(",")' <<< "$tf_output"),"

extra_vars="$(jq '{django_vars: .all_django_vars.value}' <<< "$tf_output")"

# Download Ansible roles
ansible-galaxy install \
  --force \
  --role-file=./requirements.yml \
  --roles-path=./roles

# Run Ansible playbook
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook \
  --inventory "$inventory" \
  --extra-vars "$extra_vars" \
  ./playbook.yml
