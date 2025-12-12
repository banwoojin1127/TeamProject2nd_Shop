# flask_dao/mhi_dao.py

import pymysql
import datetime
from datetime import date # datetime.date 객체 처리를 위해 추가
import pandas as pd # ⭐⭐⭐ Pandas 라이브러리 추가 ⭐⭐⭐

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
    # ... (기존 CRUD 메서드 유지) ...
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
        """나이(±5년) + 성별 동일 유저 그룹의 ID 리스트 조회"""
        cursor.execute("""
            SELECT user_id
            FROM `user` u
            WHERE u.gender = %s
              AND YEAR(u.birth) BETWEEN %s AND %s
              AND u.user_id != %s
        """, (gender, year-5, year+5, exclude_user)) 
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
                i.item_name AS product_name,
                i.item_rate, 
                i.item_reviewcnt, 
                i.item_img,
                i.item_price,
                i.item_category,
                COUNT(ph.item_id) AS purchase_count
            FROM purchase_history ph
            JOIN item i ON ph.item_id = i.item_id
            WHERE ph.user_id IN ({format_strings})
            GROUP BY ph.item_id, i.item_name, i.item_rate, i.item_reviewcnt, 
                     i.item_img, i.item_price, i.item_category
            ORDER BY purchase_count DESC -- ✅ 이 줄을 완전히 지우고 다시 입력합니다.
                    """
        cursor.execute(sql, tuple(user_list))
        return cursor.fetchall()
        
    # ------------------------------------------------------------------
    # ⭐⭐⭐ 신규: 커스텀 가중치 순위 계산 메서드 (Pandas 필요) ⭐⭐⭐
    # ------------------------------------------------------------------
    
    def apply_custom_weighted_ranking(self, recommendation_list: list, 
                                      w_rating=0.5, w_purchase=0.3, w_review=0.2):
        """
        별점, 구매 횟수, 리뷰 수에 사용자 정의 가중치를 적용하여 순위를 매깁니다.
        """
        if not recommendation_list:
            return []
            
        try:
            df = pd.DataFrame(recommendation_list)

            # 1. 데이터 타입 변환 및 결측치 처리
            df['item_rate'] = pd.to_numeric(df['item_rate'], errors='coerce').fillna(0)
            df['item_reviewcnt'] = pd.to_numeric(df['item_reviewcnt'], errors='coerce').fillna(0)
            df['purchase_count'] = pd.to_numeric(df['purchase_count'], errors='coerce').fillna(0)
            
            # 2. 정규화 (Normalization)
            max_rate = df['item_rate'].max() if df['item_rate'].max() > 0 else 1
            max_purchase = df['purchase_count'].max() if df['purchase_count'].max() > 0 else 1
            max_review = df['item_reviewcnt'].max() if df['item_reviewcnt'].max() > 0 else 1

            df['norm_rate'] = df['item_rate'] / max_rate
            df['norm_purchase'] = df['purchase_count'] / max_purchase
            df['norm_review'] = df['item_reviewcnt'] / max_review
            
            # 3. 사용자 정의 가중치(W)를 적용하여 최종 점수 계산
            df['weighted_score'] = (
                (w_rating * df['norm_rate']) +
                (w_purchase * df['norm_purchase']) +
                (w_review * df['norm_review'])
            )

            # 4. 'weighted_score' 기준으로 내림차순 정렬 및 점수 반올림
            df = df.sort_values(by='weighted_score', ascending=False)
            df['weighted_score'] = df['weighted_score'].round(4) 

            print(f"--- 디버깅 --- 커스텀 가중치 정렬 완료. W(R): {w_rating}, W(P): {w_purchase}, W(V): {w_review}")

            return df.to_dict('records')
                
        except Exception as e:
            print(f"--- 가중치 계산 중 오류 발생 (apply_custom_weighted_ranking): {e}")
            # 오류 발생 시, 정렬되지 않은 원본 리스트 반환
            return recommendation_list 

    # ------------------------------------------------------------------
    # --- 메인 추천 로직 메서드 (세 가지 리스트 반환) ---
    # ------------------------------------------------------------------

    def get_recommended_items_by_homogeneous_group(self, user_id: str, limit: int = 50):
        """나이(±5세) 및 성별 기반으로 유사 사용자들이 구매한 세 종류의 추천 목록을 딕셔너리로 반환합니다."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                # 1. 타겟 유저 정보 조회
                user_info = self.get_user_info(cursor, user_id)
                if not user_info or not user_info.get('birth') or not user_info.get('gender'):
                    return {'rating_list': [], 'purchase_list': [], 'weighted_list': []}
                
                birth_year = user_info['birth'].year 
                gender = user_info['gender']
                
                # 2. 유사 사용자 그룹 조회
                homogeneous_users = self.get_homogeneous_users(cursor, gender, birth_year, user_id)
                if not homogeneous_users:
                    return {'rating_list': [], 'purchase_list': [], 'weighted_list': []}

                # 3. 유사 그룹의 구매 내역 집계 (DB에서 1차로 구매 횟수 순으로 정렬되어 옴)
                group_purchases = self.get_purchase_history_by_users(cursor, homogeneous_users)
                if not group_purchases:
                    return {'rating_list': [], 'purchase_list': [], 'weighted_list': []}
                    
                # 4. 타겟 유저의 기구매 목록 조회
                user_purchased_items = self.get_user_purchase_items(cursor, user_id)
                
                # 5. 기구매 상품을 제외하고 초기 추천 목록 생성
                initial_recommendations = []
                for item in group_purchases:
                    if item['item_id'] not in user_purchased_items:
                        initial_recommendations.append(item)
                
                if not initial_recommendations:
                    return {'rating_list': [], 'purchase_list': [], 'weighted_list': []}
                
                # ------------------------------------------------------------------
                # ⭐ 6-A. 별점 순위 목록 (Rating Only)
                # ------------------------------------------------------------------
                rating_sorted_list = self.apply_custom_weighted_ranking(
                    initial_recommendations,
                    w_rating=1.0, w_purchase=0.0, w_review=0.0
                )

                # ------------------------------------------------------------------
                # ⭐ 6-B. 구매 횟수 순위 목록 (Purchase Only)
                # ------------------------------------------------------------------
                purchase_sorted_list = self.apply_custom_weighted_ranking(
                    initial_recommendations,
                    w_rating=0.0, w_purchase=1.0, w_review=0.0
                )

                # ------------------------------------------------------------------
                # ⭐ 6-C. 최종 가중치 순위 목록 (평점, 구매, 리뷰 통합 평가)
                # 예시 가중치 설정: w_rating=0.5, w_purchase=0.2, w_review=0.3
                # ------------------------------------------------------------------
                weighted_sorted_list = self.apply_custom_weighted_ranking(
                    initial_recommendations,
                    w_rating=0.5, w_purchase=0.2, w_review=0.3 
                )

                # 7. 세 리스트를 limit만큼 슬라이스하여 최종 딕셔너리로 반환
                final_recommendations = {
                    'rating_list': rating_sorted_list[:limit],
                    'purchase_list': purchase_sorted_list[:limit],
                    'weighted_list': weighted_sorted_list[:limit]
                }
                
                print(f"--- 디버깅 --- 최종 추천 아이템 수: {len(final_recommendations['weighted_list'])}개")
                
                return final_recommendations

        except Exception as e:
            print(f"추천 데이터 처리 오류 (최종): {e}")
            return {'rating_list': [], 'purchase_list': [], 'weighted_list': []}
            
        finally:
            conn.close()