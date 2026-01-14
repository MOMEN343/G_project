
import psycopg2

class DataBase:

    def __init__(self): 
        self.conn = psycopg2.connect(
            host="localhost",
            port=1234,
            database="g_project",
            user="postgres",
            password="2052005"
        )
        self.cur = self.conn.cursor()
        self.create_tables()

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
            document_type VARCHAR(50),
            file_path TEXT NOT NULL,
            upload_date DATE DEFAULT CURRENT_DATE,
            case_id INT NOT NULL,
            uploaded_by INT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cms.court_case(case_id),
            FOREIGN KEY (uploaded_by) REFERENCES cms.users(user_id)
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
            FOREIGN KEY (user_id) REFERENCES cms.users(user_id)
        );
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
