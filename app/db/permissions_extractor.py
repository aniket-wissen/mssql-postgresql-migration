from db.source_reader import get_connection


def extract_users() -> list:
    """
    WHY WE USE THIS:
    Extracts all database users from MSSQL.
    These need to be recreated in PostgreSQL so the same
    people/applications can access the migrated database.
    """
    print("    [Permissions Extractor] Extracting users...")
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute("""
        SELECT 
            dp.name AS username,
            dp.type_desc AS user_type
        FROM sys.database_principals dp
        WHERE dp.type IN ('S', 'U', 'G')
        AND dp.name NOT IN ('dbo', 'guest', 'INFORMATION_SCHEMA', 'sys')
        AND dp.is_fixed_role = 0
    """)
    users = cursor.fetchall()
    conn.close()
    print(f"    [Permissions Extractor] Found {len(users)} users")
    return users


def extract_roles() -> list:
    """
    WHY WE USE THIS:
    Extracts all custom roles and their members from MSSQL.
    Roles group permissions together — instead of assigning
    permissions to each user individually, users are assigned
    to roles. We need to recreate this structure in PostgreSQL.
    """
    print("    [Permissions Extractor] Extracting roles...")
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute("""
        SELECT 
            r.name AS role_name,
            m.name AS member_name
        FROM sys.database_role_members rm
        JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
        JOIN sys.database_principals m ON rm.member_principal_id = m.principal_id
        WHERE r.is_fixed_role = 0
        AND r.name NOT IN ('dbo', 'guest')
    """)
    roles = cursor.fetchall()
    conn.close()
    print(f"    [Permissions Extractor] Found {len(roles)} role memberships")
    return roles


def extract_permissions() -> list:
    """
    WHY WE USE THIS:
    Extracts all granular permissions (SELECT, INSERT, UPDATE, DELETE)
    assigned to users and roles on specific tables.
    This is the most important part of access control migration —
    without this, users would have no access to any tables
    even after being created in PostgreSQL.
    """
    print("    [Permissions Extractor] Extracting permissions...")
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute("""
        SELECT
            dp.name AS principal_name,
            dp.type_desc AS principal_type,
            perm.permission_name,
            perm.state_desc AS permission_state,
            obj.name AS object_name,
            obj.type_desc AS object_type
        FROM sys.database_permissions perm
        JOIN sys.database_principals dp ON perm.grantee_principal_id = dp.principal_id
        LEFT JOIN sys.objects obj ON perm.major_id = obj.object_id
        WHERE dp.name NOT IN ('dbo', 'guest', 'INFORMATION_SCHEMA', 'sys', 'public')
        AND dp.is_fixed_role = 0
    """)
    permissions = cursor.fetchall()
    conn.close()
    print(f"    [Permissions Extractor] Found {len(permissions)} permissions")
    return permissions


def extract_all_permissions() -> dict:
    """
    WHY WE USE THIS:
    Single entry point that extracts everything in one call.
    Returns a structured dict that gets passed to the
    permissions agent for AI-powered conversion.
    """
    print("\n[Permissions Extractor] Starting full permissions extraction...")
    return {
        "users": extract_users(),
        "roles": extract_roles(),
        "permissions": extract_permissions()
    }