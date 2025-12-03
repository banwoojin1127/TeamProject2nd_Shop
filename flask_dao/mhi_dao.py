# flask_dao/mhi_dao.py

import pymysql
import datetime
from datetime import date # datetime.date 객체 처리를 위해 추가

DB_CONFIG = {
    'host': '192.168.60.183',
    'user': 'members',
    'password': 'ezen',
    'db': 'shop',
    'charset': 'utf8mb4'
}

# ----------------------------------------------------------------------
# --- 헬퍼 함수: 나이 계산 (datetime.date 및 str 처리) ---
# ----------------------------------------------------------------------
def calculate_age(birth_date):
    """
    생년월일 (str 또는 datetime.date)로부터 현재 만 나이를 계산합니다.
    """
    if not birth_date: 
        return None
    
    birth_date_obj = None
    
    # 인수가 이미 datetime.date 객체인 경우 그대로 사용 (DB에서 가져온 경우)
    if isinstance(birth_date, date):
        birth_date_obj = birth_date
    # 인수가 문자열인 경우 변환 시도 (폼에서 받은 경우)
    elif isinstance(birth_date, str):
        try:
            birth_date_obj = datetime.datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    if birth_date_obj is None:
        return None
    
    today = date.today()
    # 만 나이 계산 로직
    age = today.year - birth_date_obj.year - (
        (today.month, today.day) < (birth_date_obj.month, birth_date_obj.day)
    )
    return age


# ----------------------------------------------------------------------
# --- MhiDAO 클래스 시작 ---
# ----------------------------------------------------------------------
class MhiDAO:
    def __init__(self):
        self.db_config = DB_CONFIG

    # ⭐ DB 연결 메서드 ⭐
    def _get_conn(self):
        return pymysql.connect(**self.db_config, cursorclass=pymysql.cursors.DictCursor)

    # ------------------------------------------------------------------
    # --- CRUD 및 인증 메서드 (통합) ---
    # ------------------------------------------------------------------

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
                return cursor.fetchall()
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM user WHERE user_id=%s", (user_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    def check_login_and_get_user(self, user_id, user_pw):
        user = self.get_user_by_id(user_id)
        # 보안 경고: 평문 비밀번호 비교를 하고 있습니다.
        if user and user_pw == user.get('user_pw'): 
            # 세션에 비밀번호를 저장하지 않도록 'user_pw' 키를 제거
            del user['user_pw']
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
            
    # ------------------------------------------------------------------
    # --- 추천 기능 헬퍼 메서드 (커서 관리를 메인 함수에 위임) ---
    # ------------------------------------------------------------------

    def get_user_info(self, cursor, user_id: str):
        """타겟 유저 정보 (생년월일, 성별) 조회"""
        cursor.execute("SELECT birth, gender FROM `user` WHERE user_id = %s", (user_id,))
        return cursor.fetchone() 

    def get_homogeneous_users(self, cursor, gender: str, year: int, exclude_user: str):
        """나이(±2년) + 성별 동일 유저 그룹의 ID 리스트 조회"""
        # 참고: 이전에 year-30, year+30으로 범위가 매우 넓었는데,
        # '나이(±2세)' 기준에 맞게 year-2, year+2로 수정했습니다.
        cursor.execute("""
            SELECT user_id
            FROM `user` u
            WHERE u.gender = %s
              AND YEAR(u.birth) BETWEEN %s AND %s
              AND u.user_id != %s
        """, (gender, year-2, year+2, exclude_user)) 
        return [r['user_id'] for r in cursor.fetchall()]

    def get_user_purchase_items(self, cursor, user_id: str):
        """특정 user의 기구매 아이템 ID 목록 조회 (Set 반환)"""
        cursor.execute("SELECT item_id FROM purchase_history WHERE user_id = %s", (user_id,))
        return {r['item_id'] for r in cursor.fetchall()}

    def get_purchase_history_by_users(self, cursor, user_list: list[str]):
        """유사 그룹의 구매 내역을 집계하여 반환"""
        if not user_list:
            return []
            
        format_strings = ','.join(['%s'] * len(user_list))
        
        sql = f"""
            SELECT 
                ph.item_id, 
                i.item_name AS product_name,  /* 템플릿과의 일관성을 위해 별칭 추가 */
                i.item_rate, 
                i.item_reviewcnt, 
                i.item_img,
                COUNT(ph.item_id) as purchase_count
            FROM purchase_history ph
            JOIN item i ON ph.item_id = i.item_id
            WHERE ph.user_id IN ({format_strings})
            GROUP BY ph.item_id, i.item_name, i.item_rate, i.item_reviewcnt, i.item_img
            ORDER BY purchase_count DESC, i.item_rate DESC
        """
        cursor.execute(sql, tuple(user_list))
        return cursor.fetchall()


    # ------------------------------------------------------------------
    # --- 메인 추천 로직 메서드 ---
    # ------------------------------------------------------------------

    def get_recommended_items_by_homogeneous_group(self, user_id: str, limit: int = 10):
        """나이(±2세) 및 성별 기반으로 유사 사용자들이 구매한 아이템을 추천합니다."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                # 1. 타겟 유저 정보 조회
                user_info = self.get_user_info(cursor, user_id)
                if not user_info or not user_info.get('birth') or not user_info.get('gender'):
                    print("--- 디버깅 --- 사용자 정보 또는 생년월일/성별 불충분")
                    return []
                
                # datetime.date 객체에서 연도 추출
                birth_year = user_info['birth'].year 
                gender = user_info['gender']
                
                # 2. 유사 사용자 그룹 조회 (나이 ±2년, 성별 동일)
                homogeneous_users = self.get_homogeneous_users(cursor, gender, birth_year, user_id)
                
                if not homogeneous_users:
                    print("--- 디버깅 --- 유사 사용자 그룹(나이±2세)을 찾지 못함")
                    return []

                # 3. 유사 그룹의 구매 내역 집계
                group_purchases = self.get_purchase_history_by_users(cursor, homogeneous_users)
                
                if not group_purchases:
                    print("--- 디버깅 --- 유사 그룹의 구매 기록이 없음")
                    return []
                    
                # 4. 타겟 유저의 기구매 목록 조회
                user_purchased_items = self.get_user_purchase_items(cursor, user_id)
                
                # 5. 기구매 상품을 제외하고 최종 추천 목록 생성
                recommended_items = []
                for item in group_purchases:
                    if item['item_id'] not in user_purchased_items:
                        recommended_items.append(item)
                        if len(recommended_items) >= limit:
                            break
                
                print(f"--- 디버깅 --- 최종 추천 아이템 수: {len(recommended_items)}")
                return recommended_items

        except Exception as e:
            print(f"추천 데이터 처리 오류 (최종): {e}")
            return []
            
        finally:
            conn.close()