
import psycopg2
import json
import os
import subprocess
import datetime


class DataBase:

    def __init__(self): 
        import socket
        current_hostname = socket.gethostname()
        target_server = "MoAlshanti"  # اسم جهازك الرئيسي
        
        # تحديد مسار ملف الإعدادات
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        # الإعدادات الذكية: إذا كان هذا هو جهازك الرئيسي، استخدم localhost، وإلا استخدم اسم جهازك في الشبكة
        if current_hostname == target_server:
            default_host = "localhost"
            default_files = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
        else:
            default_host = target_server
            default_files = f"\\\\{target_server}\\files"

        db_config = {
            "db_host": default_host,
            "db_port": 5432,
            "db_name": "g_project",
            "db_user": "postgres",
            "db_password": "2002",
            "files_path": default_files
        }
        # إذا أراد الموظف تغيير الإعدادات يدوياً عبر ملف json (اختياري)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    db_config.update(json.load(f))
            except:
                pass

        self.conn = psycopg2.connect(
            host=db_config["db_host"],
            port=db_config["db_port"],
            database=db_config["db_name"],
            user=db_config["db_user"],
            password=db_config["db_password"]
        )
        self.cur = self.conn.cursor()
        self.files_path = db_config["files_path"]

    def create_tables(self):
        
        self.cur.execute("""
        -- =====================
        -- Role Table
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.role (
            role_id SERIAL PRIMARY KEY,
            role_name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT
        );

        -- =====================
        -- Users Table
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password TEXT NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            status VARCHAR(20) DEFAULT 'ACTIVE',
            role_id INT NOT NULL,
            FOREIGN KEY (role_id) REFERENCES cms.role(role_id)
        );

        -- =====================
        -- Client Table (Passive)
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.client (
            client_id SERIAL PRIMARY KEY,

            plaintiff_name VARCHAR(100) NOT NULL,
            plaintiff_national_id VARCHAR(30),
            plaintiff_phone VARCHAR(20),

            defendant_name VARCHAR(100) NOT NULL,
            defendant_national_id VARCHAR(30),
            defendant_phone VARCHAR(20),
            defendant_address TEXT,

            case_type VARCHAR(50) NOT NULL
        );

        -- =====================
        -- Case Table
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.court_case (
            case_id SERIAL PRIMARY KEY,
            case_number VARCHAR(50) UNIQUE NOT NULL,
            case_type VARCHAR(50),
            status VARCHAR(20),
            filing_date DATE NOT NULL,
            year INT,
            description TEXT,
            created_by INT,
            FOREIGN KEY (created_by) REFERENCES cms.users(user_id)
        );

        -- =====================
        -- Case_Client (M:N)
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.case_client (
            case_id INT,
            client_id INT,
            role_in_case VARCHAR(30),
            PRIMARY KEY (case_id, client_id),
            FOREIGN KEY (case_id) REFERENCES cms.court_case(case_id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES cms.client(client_id) ON DELETE CASCADE
        );

        -- =====================
        -- Session (Hearing)
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.session (
            session_id SERIAL PRIMARY KEY,
            session_date DATE NOT NULL,
            session_time TIME NOT NULL,
            status VARCHAR(20),
            notes TEXT,
            case_id INT NOT NULL,
            judge_id INT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cms.court_case(case_id),
            FOREIGN KEY (judge_id) REFERENCES cms.users(user_id)
        );

        -- =====================
        -- Verdict (1:1)
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.verdict (
            verdict_id SERIAL PRIMARY KEY,
            verdict_date DATE NOT NULL,
            verdict_text TEXT NOT NULL,
            document_path TEXT,
            case_id INT UNIQUE NOT NULL,
            judge_id INT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cms.court_case(case_id),
            FOREIGN KEY (judge_id) REFERENCES cms.users(user_id)
        );

        -- =====================
        -- Document Table
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.document (
            document_id SERIAL PRIMARY KEY,
            document_type VARCHAR(50),         -- نوع المستند
            file_path TEXT NOT NULL,           -- مسار الملف
            upload_date DATE DEFAULT CURRENT_DATE,  -- تاريخ الرفع
            uploaded_by INT NOT NULL,          -- الموظف الذي رفع المستند
            case_id INT, 
            client_id INT,                      -- رقم القضية، يمكن تركه فارغ عند رفع المستند قبل إنشاء القضية
            FOREIGN KEY (uploaded_by) REFERENCES cms.users(user_id),
            FOREIGN KEY (case_id) REFERENCES cms.court_case(case_id),
            FOREIGN KEY (client_id) REFERENCES cms.client(client_id)
        );

        -- =====================
        -- File Transfer
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.file_transfer (
            transfer_id SERIAL PRIMARY KEY,
            transfer_date DATE DEFAULT CURRENT_DATE,
            status VARCHAR(20),
            document_id INT NOT NULL,
            sender_id INT NOT NULL,
            receiver_id INT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES cms.document(document_id),
            FOREIGN KEY (sender_id) REFERENCES cms.users(user_id),
            FOREIGN KEY (receiver_id) REFERENCES cms.users(user_id)
        );

        -- =====================
        -- Notification
        -- =====================
        CREATE TABLE IF NOT EXISTS cms.notification (
            notification_id SERIAL PRIMARY KEY,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE,
            user_id INT NOT NULL,
            document_id INT,
            FOREIGN KEY (user_id) REFERENCES cms.users(user_id),
            FOREIGN KEY (document_id) REFERENCES cms.document(document_id)
        );

        -- Ensure case_id in document table allows NULLs (for clerks workflow)
        ALTER TABLE cms.document ALTER COLUMN case_id DROP NOT NULL;
        
        -- Add plaintiff_address if not exists
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='cms' AND table_name='client' AND column_name='plaintiff_address') THEN 
                ALTER TABLE cms.client ADD COLUMN plaintiff_address TEXT; 
            END IF; 
        END $$;

        -- Add client_id to document if not exists
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='cms' AND table_name='document' AND column_name='client_id') THEN 
                ALTER TABLE cms.document ADD COLUMN client_id INT;
                ALTER TABLE cms.document ADD CONSTRAINT fk_document_client FOREIGN KEY (client_id) REFERENCES cms.client(client_id);
            END IF; 
        END $$;
        """)
        self.conn.commit()


    def execute(self, query, params=None):
        if params:
            self.cur.execute(query, params)
        else:
            self.cur.execute(query)
        self.conn.commit()


    def close(self):
        self.cur.close()
        self.conn.close()

    def backup_database(self):
        try:
            back_up_folder = r"C:\Users\TOP\Desktop\g_j\files\backup"
            os.makedirs(back_up_folder, exist_ok=True)
            today = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_file = os.path.join(back_up_folder, f"g_project_{today}.sql")

            # Need to get password from config or hardcode it since db_config is local to __init__
            # Since you know the credentials:
            db_user = "postgres"
            db_name = "g_project"
            os.environ["PGPASSWORD"] = "2002"

            import glob
            pg_dump_path = "pg_dump"
            possible_paths = glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe")
            if possible_paths:
                # Use absolute path to bypass 'not recognized' issue, and grab the latest installed version
                pg_dump_path = f'"{possible_paths[-1]}"'

            command = f'{pg_dump_path} -U {db_user} -F p {db_name} -f "{backup_file}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Backup Done ✅ File: {backup_file}")
                return True, backup_file
            else:
                print(f"Backup Failed ❌ Error: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            print(f"Backup Exception: {str(e)}")
            return False, str(e)
