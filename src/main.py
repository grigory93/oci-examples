import json
import requests
import click

BASE_URL = "https://g0e69c9e9823c87-e2v9n49xqnyq0y4z.adb.us-phoenix-1.oraclecloudapps.com/ords/admin"


@click.group()
def cli():
    """OCI ORDS REST Endpoint CLI"""
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


if __name__ == "__main__":
    cli()

