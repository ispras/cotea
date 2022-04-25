# Run cotea with docker
Images:
- cotea_container/ - image with installed cotea
- ansible_host_container/ - image acting as an Ansible host

Build both images and enter theire names into docker-compose.yaml file. After this make:
```bash
docker-compose up -d
```

After that enter into cotea container:
```bash
docker exec -it coteahost /bin/bash
```

In the container make:
```bash
cd /home/ubuntu/
python3 cotea_run.py
```

After this simple playbook will be run by cotea.
