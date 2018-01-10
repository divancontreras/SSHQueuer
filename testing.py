import config
from paramiko import SSHClient
from paramiko import AutoAddPolicy

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.load_system_host_keys()
ssh.connect(config.host, username = config.user, password = config.password)

print('started...')
stdin, stdout, stderr = ssh.exec_command('mpstat -P ALL 1', get_pty=True)

for line in iter(stdout.readline, ""):
    print(line, end="")
    print(line.split())
    print("====")
print('finished.')