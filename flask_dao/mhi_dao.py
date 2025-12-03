# flask_dao/mhi_dao.py
import pymysql

DB_CONFIG = {
    'host': '192.168.60.183',
    'user': 'members',
    'password': 'ezen',
    'db': 'shop',
    'charset': 'utf8mb4'
}

class MhiDAO:
    def __init__(self):
        self.db_config = DB_CONFIG

    def _get_conn(self):
        return pymysql.connect(**self.db_config, cursorclass=pymysql.cursors.DictCursor)

    def get_user_ids(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM user")
                result = cursor.fetchall()
                return [row['user_id'] for row in result]
        finally:
            conn.close()

    def get_all_users(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM user")
                return cursor.fetchall()  # list of dict
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
#  아이디 기준으로 모든 유저 데이터 가져오기
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM user WHERE user_id=%s", (user_id,))
                return cursor.fetchone()
        finally:
            conn.close()
#    로그인 확인 후 유저 데이터 반환
    def check_login_and_get_user(self, user_id, user_pw):
        user = self.get_user_by_id(user_id)
        if user and user_pw == user['user_pw']:
            return user
        return None



    def create_user(self, user_id, user_pw, user_name, gender=None, birth=None):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO user (user_id, user_pw, user_name, gender, birth)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, user_pw, user_name, gender, birth))
            conn.commit()
            return True
        except Exception as e:
            print("Error during user insert:", e)
            return False
        finally:
            conn.close()


# 회원가입기능 
def create_user(self, user_id, user_pw, user_name, gender=None, birth=None):
    conn = self._get_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO user (user_id, user_pw, user_name, gender, birth)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, user_pw, user_name, gender, birth))
        conn.commit()
        return True
    except Exception as e:
        print("Error during user insert:", e)
        return False
    finally:
        conn.close()

# test




