def get_permissions_conversion_prompt(permissions_data: dict) -> str:
    return f"""
You are a database access control migration expert.
Convert the following MSSQL users, roles and permissions to PostgreSQL equivalents.

Source Data:
Users: {permissions_data['users']}
Roles: {permissions_data['roles']}
Permissions: {permissions_data['permissions']}

Rules:
- MSSQL SQL_USER → PostgreSQL CREATE ROLE role_name NOLOGIN
- MSSQL DATABASE_ROLE → PostgreSQL CREATE ROLE role_name NOLOGIN
- MSSQL CONNECT permission → ignore, not needed in PostgreSQL
- MSSQL GRANT SELECT → PostgreSQL GRANT SELECT
- MSSQL GRANT INSERT → PostgreSQL GRANT INSERT
- MSSQL GRANT UPDATE → PostgreSQL GRANT UPDATE
- MSSQL dbo schema → PostgreSQL public schema
- Role memberships use GRANT role_name TO member_name
- Return ONLY valid PostgreSQL SQL statements
- Each statement on its own line ending with semicolon
- No markdown, no explanations, no code fences
- Order: CREATE ROLEs first, then GRANT memberships, then GRANT permissions

CRITICAL FORMATTING RULES:
- Always put a space between ON and the schema: GRANT SELECT ON public.table TO role
- Never write ONpublic or ONschema — always ON public or ON schema
- Double check every GRANT statement has correct spacing before returning
- Example correct format: GRANT SELECT ON public.employees TO data_reader;
- Example wrong format: GRANT SELECT ONpublic.employees TO data_reader;
"""