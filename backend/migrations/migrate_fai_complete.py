import json
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load .env from project root
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '..', '.env')
load_dotenv(env_path)

# Configuration
FAI_TENANT_ID = 'fai-003'
DB_URL = os.getenv('DATABASE_URL')

if not DB_URL:
    print("❌ ERROR: DATABASE_URL not found!")
    sys.exit(1)

# User ID mapping
user_id_map = {}

def connect_db():
    """Connect to StreemLyne database"""
    try:
        print(f"\n🔌 Connecting to database...")
        conn = psycopg2.connect(DB_URL)
        print("✅ Connected successfully!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def load_json(filename):
    """Load JSON file"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filename}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"⚠️  File is empty: {filename}")
                return None
            data = json.loads(content)
        
        if isinstance(data, dict):
            return [data]
        return data or []
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filename}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return None

def migrate_users(conn):
    """Migrate users - FAI schema to StreemLyne schema"""
    print("\n📥 Migrating Users...")
    
    users = load_json('fai_users.json')
    if not users:
        print("⏭️  No users to migrate")
        return
    
    cursor = conn.cursor()
    migrated = 0
    
    for user in users:
        try:
            email = user.get('email')
            if not email:
                continue
            
            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            existing = cursor.fetchone()
            
            # Combine first_name + last_name for full_name
            first_name = user.get('first_name') or ''
            last_name = user.get('last_name') or ''
            full_name = f"{first_name} {last_name}".strip() or email.split('@')[0]
            
            # Get password hash (try different column names)
            password = (
                user.get('password_hash') or 
                user.get('hashed_password') or 
                user.get('encrypted_password')
            )
            
            if existing:
                # Update existing user
                new_id = existing[0]
                cursor.execute("""
                    UPDATE users 
                    SET tenant_id = %s,
                        full_name = %s,
                        hashed_password = %s,
                        role = %s,
                        is_active = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    FAI_TENANT_ID,
                    full_name,
                    password,
                    user.get('role', 'staff'),
                    user.get('is_active', True),
                    new_id
                ))
            else:
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (
                        tenant_id, username, email, full_name, hashed_password, 
                        role, is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    FAI_TENANT_ID,
                    email.split('@')[0],
                    email,
                    full_name,
                    password,
                    user.get('role', 'staff'),
                    user.get('is_active', True),
                    user.get('created_at'),
                    user.get('updated_at')
                ))
                new_id = cursor.fetchone()[0]
            
            # Map old ID to new ID
            user_id_map[user.get('id')] = new_id
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating user {user.get('email')}: {e}")
            continue
    
    conn.commit()
    print(f"✅ Migrated {migrated} users")

def migrate_customers(conn):
    """Migrate customers - FAI has different schema"""
    print("\n📥 Migrating Customers...")
    
    customers = load_json('fai_customers.json')
    if not customers:
        print("⏭️  No customers to migrate")
        return
    
    cursor = conn.cursor()
    migrated = 0
    skipped = 0
    
    for customer in customers:
        try:
            # Get name
            name = customer.get('name')
            if not name:
                skipped += 1
                continue
            
            customer_id = customer.get('id')
            if not customer_id:
                customer_id = str(uuid.uuid4())
            
            # Map FAI fields to StreemLyne fields
            # FAI: sales_stage, training_stage → StreemLyne: stage
            stage = customer.get('sales_stage') or customer.get('training_stage') or 'Prospect'
            
            # Build custom_data from FAI-specific fields
            custom_data = {
                'pipeline_type': customer.get('pipeline_type'),
                'sales_stage': customer.get('sales_stage'),
                'training_stage': customer.get('training_stage'),
                'contact_made': customer.get('contact_made'),
                'preferred_contact_method': customer.get('preferred_contact_method'),
                'marketing_opt_in': customer.get('marketing_opt_in'),
                'created_by': customer.get('created_by'),
                'updated_by': customer.get('updated_by')
            }
            
            cursor.execute("""
                INSERT INTO customers (
                    id, tenant_id, name, company_name, email, phone,
                    address, postcode, stage, salesperson, notes, 
                    status, created_at, updated_at, custom_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    name = EXCLUDED.name,
                    stage = EXCLUDED.stage,
                    updated_at = NOW()
            """, (
                customer_id,
                FAI_TENANT_ID,
                name,
                name,  # Use name as company_name since FAI doesn't have separate company field
                customer.get('email') or '',
                customer.get('phone') or '',
                customer.get('address'),
                None,  # FAI doesn't have postcode
                stage,
                customer.get('salesperson') or '',
                customer.get('notes'),
                customer.get('status', 'Active'),
                customer.get('created_at'),
                customer.get('updated_at'),
                json.dumps(custom_data)
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating customer {customer.get('name')}: {e}")
            skipped += 1
            continue
    
    conn.commit()
    print(f"✅ Migrated {migrated} customers")
    if skipped > 0:
        print(f"⏭️  Skipped {skipped} customers (no name or errors)")

def migrate_test_results(conn):
    """Migrate test results"""
    print("\n📥 Migrating Test Results...")
    
    results = load_json('fai_test_results.json')
    if not results:
        print("⏭️  No test results to migrate")
        return
    
    cursor = conn.cursor()
    migrated = 0
    
    for result in results:
        try:
            # Map user ID (default to 1 if not found)
            old_user_id = result.get('user_id') or result.get('created_by')
            new_user_id = user_id_map.get(old_user_id, 1)
            
            cursor.execute("""
                INSERT INTO education_test_results (
                    tenant_id, user_id, customer_id,
                    participant_name, company, date, place, test_type,
                    mhe_type, total_marks_obtained, total_marks, 
                    percentage, grade, answers_json, details_json, 
                    image_base64, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                FAI_TENANT_ID,
                new_user_id,
                result.get('customer_id'),
                result.get('participant_name'),
                result.get('company'),
                result.get('date'),
                result.get('place'),
                result.get('test_type'),
                result.get('mhe_type'),
                result.get('total_marks_obtained'),
                result.get('total_marks'),
                result.get('percentage'),
                result.get('grade'),
                json.dumps(result.get('answers', {})) if result.get('answers') else result.get('answers_json'),
                json.dumps(result.get('details', [])) if result.get('details') else result.get('details_json'),
                result.get('image_base64'),
                result.get('created_at'),
                result.get('updated_at')
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating test result: {e}")
            continue
    
    conn.commit()
    print(f"✅ Migrated {migrated} test results")

def migrate_proposals(conn):
    """Migrate proposals"""
    print("\n📥 Migrating Proposals...")
    
    proposals = load_json('fai_proposals.json')
    if not proposals:
        print("⏭️  No proposals to migrate")
        return
    
    cursor = conn.cursor()
    migrated = 0
    
    for proposal in proposals:
        try:
            cursor.execute("""
                INSERT INTO proposals (
                    tenant_id, customer_id, reference_number, title,
                    total, status, valid_until, notes,
                    created_at, updated_at, custom_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                FAI_TENANT_ID,
                proposal.get('customer_id'),
                proposal.get('reference_number') or proposal.get('proposal_number'),
                proposal.get('title') or proposal.get('name'),
                proposal.get('total') or proposal.get('amount'),
                proposal.get('status', 'Draft'),
                proposal.get('valid_until') or proposal.get('expiry_date'),
                proposal.get('notes'),
                proposal.get('created_at'),
                proposal.get('updated_at'),
                json.dumps({})
            ))
            
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating proposal: {e}")
            continue
    
    conn.commit()
    print(f"✅ Migrated {migrated} proposals")

def verify_migration(conn):
    """Verify migration success"""
    print("\n🔍 Verifying Migration...")
    
    cursor = conn.cursor()
    
    tables = [
        'users',
        'customers',
        'education_test_results',
        'proposals'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table} 
                WHERE tenant_id = %s
            """, (FAI_TENANT_ID,))
            count = cursor.fetchone()[0]
            print(f"  ✅ {table}: {count} records")
        except Exception as e:
            print(f"  ⏭️  {table}: Not checked")

def main():
    """Run complete migration"""
    print("=" * 60)
    print("🚀 FAI to StreemLyne Complete Data Migration")
    print("=" * 60)
    print(f"📍 Target Tenant: {FAI_TENANT_ID}")
    print("=" * 60)
    
    conn = connect_db()
    
    try:
        migrate_users(conn)
        migrate_customers(conn)
        migrate_test_results(conn)
        migrate_proposals(conn)
        
        verify_migration(conn)
        
        print("\n" + "=" * 60)
        print("✅ Migration Completed Successfully!")
        print("=" * 60)
        print(f"🎯 Data migrated to tenant: {FAI_TENANT_ID}")
        print("\n📝 Next Steps:")
        print("  1. Test login with FAI credentials")
        print("  2. Verify test grading works")
        print("  3. Check customer data")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration Failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()