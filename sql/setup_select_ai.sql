-- =============================================================================
-- Oracle Autonomous AI Database - OCI Generative AI Setup
-- =============================================================================
-- Run this script in SQL Developer Web to set up OCI GenAI for Select AI
-- Access SQL Developer Web at your database URL + /ords/admin/sql-developer
-- =============================================================================

-- =============================================================================
-- STEP 1: Enable Resource Principal (Simplest for OCI)
-- =============================================================================
-- Resource Principal allows your Autonomous Database to access OCI services
-- without storing credentials. This is the recommended approach for OCI GenAI.

-- First, check if Resource Principal is already enabled
SELECT * FROM user_credentials WHERE credential_name = 'OCI$RESOURCE_PRINCIPAL';

-- Enable Resource Principal (run as ADMIN)
BEGIN
    DBMS_CLOUD_ADMIN.ENABLE_RESOURCE_PRINCIPAL();
    DBMS_OUTPUT.PUT_LINE('Resource Principal enabled successfully!');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -20000 THEN
            DBMS_OUTPUT.PUT_LINE('Resource Principal is already enabled.');
        ELSE
            RAISE;
        END IF;
END;
/

-- =============================================================================
-- STEP 2: Grant Permissions (if using a non-ADMIN user)
-- =============================================================================
-- If you're using a user other than ADMIN, grant the necessary privileges
-- Run these as ADMIN:

/*
-- Create a user for Select AI (optional - you can use ADMIN)
CREATE USER PY_CLIENT IDENTIFIED BY "YourSecurePassword123!";
GRANT CONNECT, RESOURCE TO PY_CLIENT;
GRANT DWROLE TO PY_CLIENT;  -- Required for AI features
GRANT EXECUTE ON DBMS_CLOUD_AI TO PY_CLIENT;
GRANT EXECUTE on DBMS_CLOUD_PIPELINE to PY_CLIENT;

-- Grant access to the employees table
GRANT SELECT ON ADMIN.EMPLOYEES TO PY_CLIENT;
*/

-- =============================================================================
-- STEP 3: Create the EMPLOYEES Table (if not exists)
-- =============================================================================
-- Create the employees table to match your CSV data

BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE EMPLOYEES (
            EMPNO     NUMBER(4) PRIMARY KEY,
            ENAME     VARCHAR2(50),
            JOB       VARCHAR2(50),
            MGR       NUMBER(4),
            HIREDATE  DATE,
            SAL       NUMBER(10,2),
            COMM      NUMBER(10,2),
            DEPTNO    NUMBER(2)
        )
    ';
    DBMS_OUTPUT.PUT_LINE('EMPLOYEES table created successfully!');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN  -- Table already exists
            DBMS_OUTPUT.PUT_LINE('EMPLOYEES table already exists.');
        ELSE
            RAISE;
        END IF;
END;
/

-- Insert sample employee data
BEGIN
    -- Clear existing data
    DELETE FROM EMPLOYEES;
    
    -- Insert sample employees (from your CSV)
    INSERT INTO EMPLOYEES VALUES (7839, 'REY', 'PRESIDENT', NULL, TO_DATE('11/17/1981', 'MM/DD/YYYY'), 5000, NULL, 10);
    INSERT INTO EMPLOYEES VALUES (7698, 'BLANCO', 'MANAGER', 7839, TO_DATE('05/01/1981', 'MM/DD/YYYY'), 2850, NULL, 30);
    INSERT INTO EMPLOYEES VALUES (7782, 'CLARO', 'MANAGER', 7839, TO_DATE('06/09/1981', 'MM/DD/YYYY'), 2450, NULL, 10);
    INSERT INTO EMPLOYEES VALUES (7566, 'JIMÉNEZ', 'MANAGER', 7839, TO_DATE('04/02/1981', 'MM/DD/YYYY'), 2975, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (7499, 'ALONSO', 'SALESMAN', 7698, TO_DATE('02/20/1981', 'MM/DD/YYYY'), 1600, 300, 30);
    INSERT INTO EMPLOYEES VALUES (7521, 'GUARDIA', 'SALESMAN', 7698, TO_DATE('02/22/1981', 'MM/DD/YYYY'), 1250, 500, 30);
    INSERT INTO EMPLOYEES VALUES (7654, 'MARTINE', 'SALESMAN', 7698, TO_DATE('09/28/1981', 'MM/DD/YYYY'), 1250, 1400, 30);
    INSERT INTO EMPLOYEES VALUES (7844, 'TORRES', 'SALESMAN', 7698, TO_DATE('09/08/1981', 'MM/DD/YYYY'), 1500, 0, 30);
    INSERT INTO EMPLOYEES VALUES (7900, 'SANTIAG', 'CLERK', 7698, TO_DATE('12/03/1981', 'MM/DD/YYYY'), 950, NULL, 30);
    INSERT INTO EMPLOYEES VALUES (7902, 'FUERTE', 'ANALYST', 7566, TO_DATE('12/03/1981', 'MM/DD/YYYY'), 3000, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (8080, 'CANO', 'ANALYST', 7566, TO_DATE('06/05/1983', 'MM/DD/YYYY'), 100, NULL, 20);
     -- Additional employees from Employees_original.csv
    INSERT INTO EMPLOYEES VALUES (7788, 'SCOTT', 'ANALYST', 7566, TO_DATE('12/9/1982', 'MM/DD/YYYY'), 3000, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (7369, 'SMITH', 'CLERK', 7902, TO_DATE('12/17/1980', 'MM/DD/YYYY'), 800, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (7876, 'ADAMS', 'CLERK', 7788, TO_DATE('1/12/1983', 'MM/DD/YYYY'), 1100, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (7934, 'MILLER', 'CLERK', 7782, TO_DATE('1/23/1982', 'MM/DD/YYYY'), 1300, NULL, 10);
    INSERT INTO EMPLOYEES VALUES (8100, 'KING', 'PRESIDENT', NULL, TO_DATE('11/17/1981', 'MM/DD/YYYY'), 5000, NULL, 10);
    INSERT INTO EMPLOYEES VALUES (8110, 'BLAKE', 'MANAGER', 8100, TO_DATE('5/1/1981', 'MM/DD/YYYY'), 2850, NULL, 30);
    INSERT INTO EMPLOYEES VALUES (8120, 'CLARK', 'MANAGER', 8100, TO_DATE('6/9/1981', 'MM/DD/YYYY'), 2450, NULL, 10);
    INSERT INTO EMPLOYEES VALUES (8130, 'JONES', 'MANAGER', 8100, TO_DATE('4/2/1981', 'MM/DD/YYYY'), 2975, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (8140, 'FORD', 'ANALYST', 8130, TO_DATE('12/3/1981', 'MM/DD/YYYY'), 3000, NULL, 20);
    INSERT INTO EMPLOYEES VALUES (8150, 'ALLEN', 'SALESMAN', 8110, TO_DATE('2/20/1981', 'MM/DD/YYYY'), 1600, 300, 30);
    INSERT INTO EMPLOYEES VALUES (8160, 'WARD', 'SALESMAN', 8110, TO_DATE('2/22/1981', 'MM/DD/YYYY'), 1250, 500, 30);
    INSERT INTO EMPLOYEES VALUES (8170, 'MARTIN', 'SALESMAN', 8110, TO_DATE('9/28/1981', 'MM/DD/YYYY'), 1250, 1400, 30);
    INSERT INTO EMPLOYEES VALUES (8180, 'TURNER', 'SALESMAN', 8110, TO_DATE('9/8/1981', 'MM/DD/YYYY'), 1500, 0, 30);
    INSERT INTO EMPLOYEES VALUES (8190, 'JAMES', 'CLERK', 8110, TO_DATE('12/3/1981', 'MM/DD/YYYY'), 950, NULL, 30);
    
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Employee data inserted successfully! (' || SQL%ROWCOUNT || ' rows)');
END;
/

-- Verify the data
SELECT * FROM EMPLOYEES ORDER BY EMPNO;

-- =============================================================================
-- STEP 4: Create AI Profile for OCI Generative AI
-- =============================================================================
-- This profile uses OCI GenAI with Resource Principal authentication
-- Available models in OCI GenAI (check your region for availability):
--   - cohere.command-r-plus (recommended for NL2SQL)
--   - cohere.command-r-16k
--   - meta.llama-3.1-70b-instruct
--   - meta.llama-3.1-405b-instruct

-- below we have 2 OCI compartments. Pick one depending on which cloud region we use.
-- phoenix            "oci_compartment_id": "ocid1.tenancy.oc1..aaaaaaaao2thdmij42pmo5zgxovpjijxk3nixuhgvlqbic336u3szvpqye4q",
-- chicago           "oci_compartment_id": "ocid1.tenancy.oc1..aaaaaaaaiat5tdewrwm7uvfq2bhrmbg3uqmqy7ptout2yvtua5g7cvb5wwtq",

BEGIN
    -- Drop existing profile if it exists
    BEGIN
        DBMS_CLOUD_AI.DROP_PROFILE(profile_name => 'OCI_GENAI_PROFILE');
        DBMS_OUTPUT.PUT_LINE('Dropped existing profile.');
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- Create AI profile for OCI Generative AI
    DBMS_CLOUD_AI.CREATE_PROFILE(
        profile_name => 'OCI_GENAI_PROFILE',
        attributes   => '{
            "provider": "oci",
            "credential_name": "OCI$RESOURCE_PRINCIPAL",
            "model": "cohere.command-r-plus",

            "oci_compartment_id": "ocid1.tenancy.oc1..aaaaaaaao2thdmij42pmo5zgxovpjijxk3nixuhgvlqbic336u3szvpqye4q",
            "oci_compartment_id": "ocid1.tenancy.oc1..aaaaaaaaiat5tdewrwm7uvfq2bhrmbg3uqmqy7ptout2yvtua5g7cvb5wwtq",
            "object_list": [
                {"owner": "ADMIN", "name": "EMPLOYEES"}
            ]
        }'
    );
    
    DBMS_OUTPUT.PUT_LINE('OCI GenAI profile created successfully!');
END;
/

-- =============================================================================
-- STEP 5: Set Default Profile and Test
-- =============================================================================

-- Set the AI profile as default for the session
EXEC DBMS_CLOUD_AI.SET_PROFILE('OCI_GENAI_PROFILE');
BEGIN
    DBMS_CLOUD_AI.SET_PROFILE(profile_name => 'OCI_GENAI_PROFILE');
END;

-- Verify profile is set
SELECT DBMS_CLOUD_AI.GET_PROFILE() AS CURRENT_PROFILE FROM DUAL;

-- =============================================================================
-- STEP 6: Test Select AI Queries
-- =============================================================================

-- Test 1: Simple count
SELECT AI 'How many employees are there?';

-- Test 2: Show the generated SQL
SELECT AI SHOWSQL 'List all employees in department 30';

-- Test 3: Filtered query
SELECT AI 'Who are the managers?';

-- Test 4: Aggregation
SELECT AI 'What is the average salary by job?';

-- Test 5: Narrate results
SELECT AI NARRATE 'Summarize the salary distribution';

-- Test 6: Chat (non-SQL)
SELECT AI CHAT 'What columns are in the EMPLOYEES table?';

-- =============================================================================
-- Troubleshooting
-- =============================================================================

-- Check available AI profiles
SELECT profile_name, status, description 
FROM user_cloud_ai_profiles;

-- Check credentials
SELECT credential_name, username, enabled 
FROM all_credentials 
WHERE credential_name LIKE '%RESOURCE%' OR credential_name LIKE '%OCI%';

-- Check if GenAI is accessible (should return available models)
-- Note: This requires proper IAM policies in your OCI tenancy
/*
SELECT DBMS_CLOUD_AI.GET_AVAILABLE_MODELS('oci') FROM DUAL;
*/

-- =============================================================================
-- IMPORTANT: OCI IAM Policy Required
-- =============================================================================
-- For Resource Principal to work with OCI Generative AI, you need to add
-- an IAM policy in your OCI tenancy. Go to:
-- OCI Console > Identity & Security > Policies
-- 
-- Add a policy with this statement (adjust compartment name as needed):
/*
Allow any-user to manage generative-ai-family in compartment YOUR_COMPARTMENT_NAME where request.principal.type = 'autonomousdatabase'
*/
-- Or more restrictively:
/*
Allow dynamic-group YOUR_ADB_DYNAMIC_GROUP to manage generative-ai-family in compartment YOUR_COMPARTMENT_NAME
*/
