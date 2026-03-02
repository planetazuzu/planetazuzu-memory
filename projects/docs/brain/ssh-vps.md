```bash
mkdir -p ~/.ssh/sockets && ssh -o ControlMaster=auto -o ControlPath=~/.ssh/sockets/%r@%h-%p -o ControlPersist=600 root@207.180.226.141
```
