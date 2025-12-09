import json
import os
import requests
import click
import oracledb
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "https://g0e69c9e9823c87-e2v9n49xqnyq0y4z.adb.us-phoenix-1.oraclecloudapps.com/ords/admin"

# Default DSN - get the TLS connection string from OCI Console > Database Connection
DEFAULT_DSN = os.getenv("ORACLE_DB_DSN", "")
DEFAULT_USER = os.getenv("ORACLE_DB_USER", "ADMIN")
DEFAULT_PASSWORD = os.getenv("ORACLE_DB_PASSWORD", "")


@click.group()
def cli():
    """OCI Autonomous Database CLI - Test various connection methods"""
    pass


@cli.command()
@click.option('--base-url', default=BASE_URL, help='Base URL for ORDS endpoint')
@click.option('--verify/--no-verify', default=False, help='Verify SSL certificates')
def test_open_api_catalog(base_url, verify):
    """Test the ORDS Open API Catalog endpoint"""
    url = f"{base_url}/open-api-catalog/"
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"}, verify=verify)
        
        click.echo(f"Status Code: {response.status_code}")
        click.echo("Response:")
        
        print(json.dumps(response.json(), indent=2))
            
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option('--user', '-u', default=DEFAULT_USER, help='Database username')
@click.option('--password', '-p', default=DEFAULT_PASSWORD, help='Database password (or set in .env file)')
@click.option('--dsn', '-d', default=DEFAULT_DSN, help='Database DSN/connection string (or set in .env file)')
@click.option('--wallet', '-w', is_flag=True, default=False, help='Use wallet from ORACLE_WALLET_LOCATION env var (enables mTLS mode)')
@click.option('--query', '-q', default="SELECT SYSDATE, USER FROM DUAL", help='SQL query to execute')
def test_tls_connection(user, password, dsn, wallet, query):
    """Test database connection using python-oracledb Thin Mode.
    
    By default uses TLS (no wallet). Specify --wallet to use mTLS with wallet.
    
    Examples:
    
    \b
    # TLS connection (no wallet):
    python -m src.main test-tls-connection
    
    \b
    # mTLS with wallet from ORACLE_WALLET_LOCATION env var:
    python -m src.main test-tls-connection --wallet
    python -m src.main test-tls-connection -w
    
    \b
    # Run a custom query:
    python -m src.main test-tls-connection --query "SELECT * FROM EMPLOYEES"
    """
    if not dsn:
        click.echo("Error: DSN is required. Set ORACLE_DB_DSN in .env file, env var, or use --dsn option.", err=True)
        click.echo("\nTo get your DSN:", err=True)
        click.echo("  1. Go to OCI Console > Autonomous Database > Your Database", err=True)
        click.echo("  2. Click 'Database Connection'", err=True)
        click.echo("  3. Copy the TLS connection string", err=True)
        raise SystemExit(1)
    
    if not password:
        click.echo("Error: Password is required. Set ORACLE_DB_PASSWORD in .env file, env var, or use --password option.", err=True)
        raise SystemExit(1)
    
    # Get wallet path from env var if --wallet flag is set
    wallet_path = None
    if wallet:
        wallet_path = os.getenv("ORACLE_WALLET_LOCATION", "")
        if not wallet_path:
            click.echo("Error: --wallet requires ORACLE_WALLET_LOCATION env var to be set.", err=True)
            click.echo("  Set it in your .env file or environment.", err=True)
            raise SystemExit(1)
    
    click.echo("=" * 60)
    if wallet_path:
        click.echo("Testing Oracle Database Connection (Thin Mode + mTLS/Wallet)")
    else:
        click.echo("Testing Oracle Database Connection (Thin Mode + TLS)")
    click.echo("=" * 60)
    click.echo(f"User: {user}")
    click.echo(f"DSN:  {dsn[:60]}..." if len(dsn) > 60 else f"DSN:  {dsn}")
    if wallet_path:
        click.echo(f"Wallet: {wallet_path}")
    click.echo("-" * 60)
    
    try:
        # Connect using Thin mode
        if wallet_path:
            # mTLS connection with wallet
            connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn,
                config_dir=wallet_path,
                wallet_location=wallet_path,
                wallet_password=os.getenv("ORACLE_WALLET_PASSWORD", "")
            )
        else:
            # TLS connection without wallet
            connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn
            )
        
        click.echo(click.style("✓ Connected successfully!", fg="green"))
        click.echo(f"  Database Version: {connection.version}")
        click.echo(f"  Thin Mode: {connection.thin}")
        
        # Execute the query
        click.echo(f"\nExecuting: {query}")
        click.echo("-" * 60)
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            
            # Get column names
            columns = [col[0] for col in cursor.description]
            click.echo("  " + " | ".join(columns))
            click.echo("  " + "-" * (len(" | ".join(columns))))
            
            # Fetch and display results
            rows = cursor.fetchall()
            for row in rows:
                formatted_row = [str(val) if val is not None else "NULL" for val in row]
                click.echo("  " + " | ".join(formatted_row))
            
            click.echo(f"\n✓ Query returned {len(rows)} row(s)")
        
        connection.close()
        click.echo(click.style("\n✓ Connection closed successfully!", fg="green"))
        
    except oracledb.Error as e:
        error, = e.args
        click.echo(click.style(f"\n✗ Database Error: {error.message}", fg="red"), err=True)
        click.echo(f"  Error Code: {error.code}", err=True)
        
        # Provide helpful troubleshooting tips
        if "DPY-6000" in str(error.message) or "Listener refused" in str(error.message):
            click.echo("\n" + "=" * 60, err=True)
            click.echo("Troubleshooting Tips:", err=True)
            click.echo("=" * 60, err=True)
            click.echo("1. TLS-only connections may not be enabled on your database.", err=True)
            click.echo("   → Go to OCI Console > Autonomous Database > Your DB", err=True)
            click.echo("   → Edit 'Mutual TLS (mTLS) Authentication'", err=True)
            click.echo("   → UNCHECK 'Require mutual TLS (mTLS) authentication'", err=True)
            click.echo("   → Save and wait a few minutes for changes to apply", err=True)
            click.echo("", err=True)
            click.echo("2. Or use wallet-based connection (mTLS):", err=True)
            click.echo("   → Download wallet from OCI Console > Database Connection", err=True)
            click.echo("   → Unzip to a folder (e.g., ~/wallet)", err=True)
            click.echo("   → Run: test-tls-connection --wallet ~/wallet", err=True)
            click.echo("", err=True)
            click.echo("3. Check Access Control List (ACL):", err=True)
            click.echo("   → Go to OCI Console > Autonomous Database > Your DB", err=True)
            click.echo("   → Under Network, edit 'Access Control List'", err=True)
            click.echo("   → Add your IP or allow access from anywhere", err=True)
        
        raise SystemExit(1)


@cli.command()
@click.option('--user', '-u', default=DEFAULT_USER, help='Database username')
@click.option('--password', '-p', default=DEFAULT_PASSWORD, help='Database password (or set in .env file)')
@click.option('--dsn', '-d', default=DEFAULT_DSN, help='Database DSN/connection string (or set in .env file)')
@click.option('--wallet', '-w', is_flag=True, default=False, help='Use wallet from ORACLE_WALLET_LOCATION env var')
def list_tables(user, password, dsn, wallet):
    """List all tables in the current schema."""
    if not dsn or not password:
        click.echo("Error: DSN and password are required.", err=True)
        raise SystemExit(1)
    
    # Get wallet path from env var if --wallet flag is set
    wallet_path = None
    if wallet:
        wallet_path = os.getenv("ORACLE_WALLET_LOCATION", "")
        if not wallet_path:
            click.echo("Error: --wallet requires ORACLE_WALLET_LOCATION env var to be set.", err=True)
            raise SystemExit(1)
    
    query = """
        SELECT table_name, num_rows, last_analyzed 
        FROM user_tables 
        ORDER BY table_name
    """
    
    try:
        if wallet_path:
            connection = oracledb.connect(
                user=user, password=password, dsn=dsn,
                config_dir=wallet_path, wallet_location=wallet_path,
                wallet_password=os.getenv("ORACLE_WALLET_PASSWORD", "")
            )
        else:
            connection = oracledb.connect(user=user, password=password, dsn=dsn)
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            click.echo(f"\nTables in schema {user}:")
            click.echo("-" * 60)
            click.echo(f"{'TABLE_NAME':<30} {'NUM_ROWS':<12} {'LAST_ANALYZED'}")
            click.echo("-" * 60)
            
            for row in rows:
                table_name, num_rows, last_analyzed = row
                num_rows_str = str(num_rows) if num_rows is not None else "N/A"
                last_analyzed_str = str(last_analyzed)[:19] if last_analyzed else "Never"
                click.echo(f"{table_name:<30} {num_rows_str:<12} {last_analyzed_str}")
            
            click.echo(f"\nTotal: {len(rows)} table(s)")
        
        connection.close()
        
    except oracledb.Error as e:
        error, = e.args
        click.echo(click.style(f"Error: {error.message}", fg="red"), err=True)
        raise SystemExit(1)


@cli.command()
@click.option('--user', '-u', default=DEFAULT_USER, help='Database username')
@click.option('--password', '-p', default=DEFAULT_PASSWORD, help='Database password (or set in .env file)')
@click.option('--dsn', '-d', default=DEFAULT_DSN, help='Database DSN/connection string (or set in .env file)')
@click.option('--wallet', '-w', is_flag=True, default=False, help='Use wallet from ORACLE_WALLET_LOCATION env var')
def show_employees(user, password, dsn, wallet):
    """Display all employees from the EMPLOYEES table."""
    if not dsn or not password:
        click.echo("Error: DSN and password are required.", err=True)
        raise SystemExit(1)
    
    # Get wallet path from env var if --wallet flag is set
    wallet_path = None
    if wallet:
        wallet_path = os.getenv("ORACLE_WALLET_LOCATION", "")
        if not wallet_path:
            click.echo("Error: --wallet requires ORACLE_WALLET_LOCATION env var to be set.", err=True)
            raise SystemExit(1)
    
    query = "SELECT EMPNO, ENAME, JOB, SAL, DEPTNO FROM EMPLOYEES ORDER BY SAL DESC"
    
    try:
        if wallet_path:
            connection = oracledb.connect(
                user=user, password=password, dsn=dsn,
                config_dir=wallet_path, wallet_location=wallet_path,
                wallet_password=os.getenv("ORACLE_WALLET_PASSWORD", "")
            )
        else:
            connection = oracledb.connect(user=user, password=password, dsn=dsn)
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            click.echo("\nEmployees (sorted by salary):")
            click.echo("-" * 60)
            click.echo(f"{'EMPNO':<8} {'ENAME':<12} {'JOB':<12} {'SAL':>10} {'DEPTNO':>8}")
            click.echo("-" * 60)
            
            for row in rows:
                empno, ename, job, sal, deptno = row
                sal_str = f"{sal:,.2f}" if sal else "N/A"
                click.echo(f"{empno:<8} {ename:<12} {job:<12} {sal_str:>10} {deptno:>8}")
            
            click.echo(f"\nTotal: {len(rows)} employee(s)")
        
        connection.close()
        
    except oracledb.Error as e:
        error, = e.args
        if error.code == 942:  # Table doesn't exist
            click.echo(click.style("Error: EMPLOYEES table does not exist.", fg="red"), err=True)
            click.echo("Run the setup_credentials.sql script first to create and populate the table.", err=True)
        else:
            click.echo(click.style(f"Error: {error.message}", fg="red"), err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()

