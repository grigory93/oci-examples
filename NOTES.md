# Notes

## Provisioning

### Dedicated AI Cluster

Home -> Generative AI -> Endpoints, Dedicated AI clusters

Not possible to create due to Error 400 : LimitExceeded Failed to create, The following service limits were exceeded: dedicated-unit-large-cohere-count. You can request a service limit increase from the Console's Limits, Quotas and Usage page or from the Help menu.


## OCI Object Storage

To store raw CSV files

Source of data: http://www.tableau.com/sites/default/files/training/global_superstore.zip

Object store bucket: https://objectstorage.us-phoenix-1.oraclecloud.com/n/axho97fnj9bu/b/corp-order-data/o/global-superstore-orders.csv

Object store URL for Data Transform: https://axho97fnj9bu.objectstorage.us-phoenix-1.oci.customer-oci.com/n/axho97fnj9bu/b/corp-order-data/o

Auth Token: +dNMP;g1:wMmg:kYiuA8 
(Found User Domain Token in Security and Identity -> Domains -> Users -> Auth Tokens)

Oracle Data Transforms: https://G0E69C9E9823C87-E2V9N49XQNYQ0Y4Z.adb.us-phoenix-1.oraclecloudapps.com/odi/



Autonomous AI Database Data Load: https://g0e69c9e9823c87-e2v9n49xqnyq0y4z.adb.us-phoenix-1.oraclecloudapps.com/ords/admin/_sdw/?nav=adpdi&adpdi=adp-data-load#



## VM Config

Ubuntu 24.04 Minimal on Ampere A1 (Always Free tier eligible)

### SSH Access

```bash
chmod 600 ~/.ssh/your-key.pem
ssh -i ~/.ssh/your-key.pem ubuntu@<public-ip>
```

### Install Python

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip -y
```

### Install UFW

```bash
sudo apt install ufw -y
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### OCI Security List (Console)

Add Ingress Rules on public subnet:
- TCP 22 (SSH)
- TCP 80 (HTTP)
- TCP 443 (HTTPS)
- TCP 8000 (App)
- ICMP Type 8 (Ping)

### iptables (OCI Ubuntu has REJECT rule that blocks ports)

```bash
# Insert rules BEFORE the REJECT rule (position 5)
sudo iptables -I INPUT 5 -p tcp --dport 80 -m state --state NEW -j ACCEPT
sudo iptables -I INPUT 5 -p tcp --dport 443 -m state --state NEW -j ACCEPT
sudo iptables -I INPUT 5 -p tcp --dport 8000 -m state --state NEW -j ACCEPT

# Save rules permanently
sudo apt install netfilter-persistent -y
sudo netfilter-persistent save
```

### Verify iptables

```bash
sudo iptables -L INPUT -n --line-numbers
# Port rules must appear BEFORE the REJECT rule
```

### Test Port Access

```bash
# On VM
python3 -m http.server 8000

# From local machine
curl http://<public-ip>:8000
```


## MCP

### Cloud VM Deployment
When you deploy to your VM:
Copy the project
Set environment variables in .env:
ORACLE_DB_DSN
ORACLE_DB_PASSWORD
ORACLE_DB_USER (optional, defaults to ADMIN)

Open firewall port 8000

Run: uv run python -m src.mcp_server


## Python on VM

### Copy file
```bash
scp -i ~/.ssh/your-key.pem -r ~/wallet/Wallet_E2V9N49XQNYQ0Y4Z ubuntu@64.181.210.109:~/wallet/
```

```bash
scp .env ubuntu@oci-dev-vm:~/oci-demo/
```