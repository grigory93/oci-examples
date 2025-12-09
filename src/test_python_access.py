"""
Oracle Autonomous AI Database - Select AI for Python Demo
==========================================================

This script demonstrates how to use Oracle Select AI to interact with
your database using natural language queries.

Prerequisites:
1. Install required packages: pip install select_ai oracledb pandas
2. Set up AI provider credentials in the database (see setup_credentials.sql)
3. Have your database connection details ready
"""

import os
from dataclasses import dataclass

# =============================================================================
# Configuration
# =============================================================================
@dataclass
class DBConfig:
    """Database configuration settings"""
    user: str = "ADMIN"
    password: str = os.getenv("ORACLE_DB_PASSWORD", "YourSecurePassword")
    
    # Connection options (choose one):
    # Option 1: DSN from wallet (e.g., "dbname_high")
    # Option 2: Full connection string for TLS without wallet
    dsn: str = os.getenv("ORACLE_DB_DSN", "your_db_dsn")
    
    # For wallet-based connection
    wallet_location: str = os.getenv("ORACLE_WALLET_LOCATION", "")
    wallet_password: str = os.getenv("ORACLE_WALLET_PASSWORD", "")
    
    # AI Provider settings (using OCI Generative AI with Resource Principal)
    ai_credential_name: str = "OCI$RESOURCE_PRINCIPAL"
    ai_profile_name: str = "OCI_GENAI_PROFILE"
    
    # OCI compartment for GenAI (get from OCI Console)
    oci_compartment_id: str = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID")


# =============================================================================
# Step 1: Basic Database Connection Test (using oracledb directly)
# =============================================================================
def test_basic_connection(config: DBConfig) -> bool:
    """Test basic database connectivity using oracledb driver"""
    import oracledb
    
    print("\n" + "=" * 60)
    print("Step 1: Testing Basic Database Connection")
    print("=" * 60)
    
    try:
        # Connect without wallet (TLS)
        if not config.wallet_location:
            connection = oracledb.connect(
                user=config.user,
                password=config.password,
                dsn=config.dsn
            )
        else:
            # Connect with wallet (mTLS)
            connection = oracledb.connect(
                user=config.user,
                password=config.password,
                dsn=config.dsn,
                config_dir=config.wallet_location,
                wallet_location=config.wallet_location,
                wallet_password=config.wallet_password
            )
        
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT SYSDATE, USER FROM DUAL")
            result = cursor.fetchone()
            print(f"✓ Connected successfully!")
            print(f"  Database Time: {result[0]}")
            print(f"  Connected User: {result[1]}")
        
        connection.close()
        return True
        
    except oracledb.Error as e:
        print(f"✗ Connection failed: {e}")
        return False


# =============================================================================
# Step 2: Connect using Select AI
# =============================================================================
def connect_select_ai(config: DBConfig):
    """Establish connection using select_ai library"""
    import select_ai
    
    print("\n" + "=" * 60)
    print("Step 2: Connecting with Select AI")
    print("=" * 60)
    
    try:
        select_ai.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn
        )
        print("✓ Select AI connected successfully!")
        return True
    except Exception as e:
        print(f"✗ Select AI connection failed: {e}")
        return False


# =============================================================================
# Step 3: Create AI Profile
# =============================================================================
def create_ai_profile(config: DBConfig, provider_type: str = "oci"):
    """Create an AI profile for natural language queries"""
    import select_ai
    
    print("\n" + "=" * 60)
    print("Step 3: Creating AI Profile")
    print("=" * 60)
    
    try:
        if provider_type == "openai":
            provider = select_ai.OpenAIProvider(
                model="gpt-4o-mini"  # Cost-effective option
            )
            print("  Using OpenAI provider (gpt-4o-mini)")
            
        elif provider_type == "oci":
            provider = select_ai.OCIGenAIProvider(
                region="us-phoenix-1",  # Adjust to your region
                model="cohere.command-r-plus",
                oci_compartment_id=config.oci_compartment_id
            )
            print("  Using OCI Generative AI provider (cohere.command-r-plus)")
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        profile_attributes = select_ai.ProfileAttributes(
            credential_name=config.ai_credential_name,
            provider=provider
        )
        
        profile = select_ai.Profile(
            profile_name=config.ai_profile_name,
            attributes=profile_attributes,
            description="Select AI Profile for natural language queries",
            replace=True
        )
        
        print(f"✓ AI Profile '{config.ai_profile_name}' created successfully!")
        return profile
        
    except Exception as e:
        print(f"✗ Failed to create AI profile: {e}")
        return None


# =============================================================================
# Step 4: Natural Language to SQL Examples
# =============================================================================
def demo_natural_language_queries(profile):
    """Demonstrate natural language to SQL conversion"""
    
    print("\n" + "=" * 60)
    print("Step 4: Natural Language Query Examples")
    print("=" * 60)
    
    # Sample queries for the EMPLOYEES table
    queries = [
        "How many employees are there?",
        "Show me all employees in department 30",
        "What is the average salary by job?",
        "Who are the top 3 highest paid employees?",
        "List all managers with their salaries",
    ]
    
    for i, question in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"📝 Question: {question}")
        
        try:
            # Get generated SQL
            sql = profile.showsql(prompt=question)
            print(f"🔧 Generated SQL: {sql}")
            
            # Execute and get results
            df = profile.run_sql(prompt=question)
            print(f"📊 Results:")
            print(df.to_string(index=False))
            
        except Exception as e:
            print(f"⚠️  Error: {e}")


# =============================================================================
# Step 5: Interactive Chat with AI
# =============================================================================
def demo_chat(profile):
    """Demonstrate chat functionality"""
    
    print("\n" + "=" * 60)
    print("Step 5: Chat with AI")
    print("=" * 60)
    
    questions = [
        "What columns are in the EMPLOYEES table?",
        "Explain the difference between ANALYST and MANAGER jobs",
    ]
    
    for question in questions:
        print(f"\n💬 You: {question}")
        try:
            response = profile.chat(prompt=question)
            print(f"🤖 AI: {response}")
        except Exception as e:
            print(f"⚠️  Error: {e}")


# =============================================================================
# Step 6: Describe/Narrate Results
# =============================================================================
def demo_narrate(profile):
    """Demonstrate result narration"""
    
    print("\n" + "=" * 60)
    print("Step 6: Narrate Query Results")
    print("=" * 60)
    
    try:
        question = "Summarize the salary distribution across departments"
        print(f"📝 Question: {question}")
        
        response = profile.runsql_chat(prompt=question)
        print(f"📖 Narrative: {response}")
        
    except Exception as e:
        print(f"⚠️  Error: {e}")


# =============================================================================
# Alternative: Direct SQL with DBMS_CLOUD_AI (without select_ai package)
# =============================================================================
def demo_direct_sql_select_ai(config: DBConfig):
    """Use Select AI directly through SQL (alternative approach)"""
    import oracledb
    
    print("\n" + "=" * 60)
    print("Alternative: Direct SQL with Select AI")
    print("=" * 60)
    
    try:
        connection = oracledb.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn
        )
        
        cursor = connection.cursor()
        
        # Set the AI profile to use
        cursor.execute(f"""
            BEGIN
                DBMS_CLOUD_AI.SET_PROFILE('{config.ai_profile_name}');
            END;
        """)
        
        # Execute Select AI query
        question = "How many employees earn more than 2000?"
        print(f"📝 Question: {question}")
        
        cursor.execute(f"SELECT AI '{question}'")
        
        for row in cursor:
            print(f"📊 Result: {row}")
        
        connection.close()
        
    except oracledb.Error as e:
        print(f"⚠️  Error: {e}")


# =============================================================================
# Main Execution
# =============================================================================
def main():
    """Main entry point for the demo"""
    
    print("=" * 60)
    print("Oracle Autonomous AI Database - Select AI Demo")
    print("=" * 60)
    
    # Initialize configuration
    config = DBConfig()
    
    print("\nConfiguration:")
    print(f"  User: {config.user}")
    print(f"  DSN: {config.dsn[:50]}..." if len(config.dsn) > 50 else f"  DSN: {config.dsn}")
    print(f"  AI Credential: {config.ai_credential_name}")
    print(f"  AI Profile: {config.ai_profile_name}")
    
    # Step 1: Test basic connection
    if not test_basic_connection(config):
        print("\n⚠️  Cannot proceed without database connection.")
        print("Please check your connection settings and try again.")
        return
    
    # Step 2: Connect with Select AI
    if not connect_select_ai(config):
        print("\n⚠️  Select AI connection failed.")
        print("Make sure 'select_ai' package is installed: pip install select_ai")
        return
    
    # Step 3: Create AI Profile (using OCI Generative AI)
    profile = create_ai_profile(config, provider_type="oci")
    if not profile:
        print("\n⚠️  Could not create AI profile.")
        print("Make sure you have:")
        print("  1. Enabled Resource Principal in the database")
        print("  2. Added the required IAM policy in OCI")
        print("  3. Set the correct OCI_COMPARTMENT_ID")
        return
    
    # Step 4: Natural Language Queries
    demo_natural_language_queries(profile)
    
    # Step 5: Chat with AI
    demo_chat(profile)
    
    # Step 6: Narrate Results
    demo_narrate(profile)
    
    print("\n" + "=" * 60)
    print("✓ Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

