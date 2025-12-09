# OCI Autonomous Database Demo

A Python CLI for connecting to Oracle Autonomous AI Database using various methods.

## Features

- **TLS Connection**: Direct connection without wallet (requires mTLS to be disabled)
- **mTLS Connection**: Secure connection using wallet credentials
- **ORDS REST API**: Test REST endpoints
- **Select AI**: Natural language to SQL queries (coming soon)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd oci-demo

# Install dependencies using uv
uv sync
```

## Configuration

Create a `.env` file in the project root with your database credentials:

```bash
# Database credentials
ORACLE_DB_USER=ADMIN
ORACLE_DB_PASSWORD=YourSecurePassword

# Connection string (get from OCI Console > Database Connection > TLS)
ORACLE_DB_DSN=(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.us-phoenix-1.oraclecloud.com))(connect_data=(service_name=xxx_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))

# Optional: Wallet location for mTLS connections
ORACLE_WALLET_LOCATION=/path/to/wallet
ORACLE_WALLET_PASSWORD=wallet_password
```

## CLI Commands

### Show All Commands

```bash
uv run python -m src.main --help
```

---

### `test-tls-connection`

Test database connectivity using python-oracledb in Thin Mode.

**TLS Mode (no wallet):**
```bash
uv run python -m src.main test-tls-connection
```

**mTLS Mode (wallet from env var):**
```bash
# Uses ORACLE_WALLET_LOCATION from .env
uv run python -m src.main test-tls-connection --wallet
uv run python -m src.main test-tls-connection -w
```

**With custom query:**
```bash
uv run python -m src.main test-tls-connection --query "SELECT * FROM EMPLOYEES"
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--user` | `-u` | Database username (default: from .env) |
| `--password` | `-p` | Database password (default: from .env) |
| `--dsn` | `-d` | Connection string (default: from .env) |
| `--wallet` | `-w` | Enable mTLS using wallet from `ORACLE_WALLET_LOCATION` |
| `--query` | `-q` | SQL query to execute |

---

### `list-tables`

List all tables in the current schema.

```bash
# TLS mode
uv run python -m src.main list-tables

# mTLS with wallet from env var
uv run python -m src.main list-tables --wallet
uv run python -m src.main list-tables -w
```

---

### `show-employees`

Display all employees from the EMPLOYEES table (sorted by salary).

```bash
# TLS mode
uv run python -m src.main show-employees

# mTLS with wallet from env var
uv run python -m src.main show-employees --wallet
uv run python -m src.main show-employees -w
```

---

### `test-open-api-catalog`

Test the ORDS Open API Catalog REST endpoint.

```bash
uv run python -m src.main test-open-api-catalog
```

**Options:**
| Option | Description |
|--------|-------------|
| `--base-url` | Base URL for ORDS endpoint |
| `--verify/--no-verify` | Verify SSL certificates |

---

## Connection Methods

### Option 1: TLS (No Wallet) - Simplest

Requires disabling mTLS requirement in OCI Console:

1. Go to **OCI Console** → **Autonomous Database** → Your database
2. Click **Edit** next to **Mutual TLS (mTLS) Authentication**
3. **Uncheck** "Require mutual TLS (mTLS) authentication"
4. Save and wait 2-3 minutes

Then connect:
```bash
uv run python -m src.main test-tls-connection
```

### Option 2: mTLS (With Wallet) - Default Security

1. Download wallet from **OCI Console** → **Database Connection** → **Download wallet**
2. Unzip to a folder:
   ```bash
   mkdir ~/wallet
   unzip Wallet_*.zip -d ~/wallet
   ```
3. Set the wallet location in your `.env`:
   ```bash
   ORACLE_WALLET_LOCATION=/Users/yourname/wallet
   ```
4. Connect with wallet:
   ```bash
   uv run python -m src.main test-tls-connection --wallet
   ```

---

## Troubleshooting

### DPY-6000: Listener refused connection

This error means TLS-only connections are not enabled. Either:

1. **Enable TLS-only**: Disable mTLS requirement in OCI Console (see above)
2. **Use wallet**: Download and use wallet for mTLS connection
3. **Check ACL**: Ensure your IP is allowed in Access Control List

### Table does not exist

Run the setup SQL script first:
```bash
# Open SQL Developer Web and run src/setup_credentials.sql
```

---

## Project Structure

```
oci-demo/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI commands
│   ├── test_python_access.py   # Select AI demo (advanced)
│   ├── setup_credentials.sql   # Database setup script
│   └── env_example.txt         # Environment variables template
├── data/
│   └── employees.csv           # Sample data
├── pyproject.toml
├── .env                        # Your credentials (not in git)
└── README.md
```

---

## License

MIT

