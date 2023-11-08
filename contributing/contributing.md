# Contributing
For development purposes you have to be able to run Ansible. If you don't have Ansible host, inventory files and etc, or you don't want to run Ansible against your hosts in cotea development purposes, there is a guide below for you.

1. Run Ansible host
(our special container)

```bash
docker run --name ans_host --rm -d -p 2222:22 dbadalyan/ansible_host_for_cotea /path/to/your/public_key.pub
```
Port 2222 is used here as a *ansible_ssh_port*. You can use the preferred one.

2. Get required files

If you have your own inventory or playbook files - you can use ones instead.

Clone cotea repo:
```bash
git clone https://github.com/ispras/cotea
```

You need an inventory file:
```bash
cp cotea/docs/contributing/contr_inv contr_inv
```
*ansible_port* is 2222 in this file, set the preferred one if you changed it in *docker run* command.

Playbook file:
```bash
cp cotea/docs/contributing/contr_pb.yaml contr_pb.yaml
```

Python file with cotea imports and Ansible launch:
```bash
cp cotea/docs/contributing/cotea_ansible_run.py cotea_ansible_run.py
```

3. Run Ansible using cotea

```bash
python3 cotea_ansible_run.py
```
