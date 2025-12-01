import pymysql

class LshDAO :
    def __init__(self) :
        self.conn = pymysql.connect(
            host="192.168.60.183",
            user="members",
            password="ezen",
            database="shop",
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()

    def close(self):
        # 커서 닫기 (이미 닫혔으면 무시)
        if hasattr(self, 'cursor') and self.cursor:
            try:
                self.cursor.close()
            except Exception:
                pass
            self.cursor = None

        # 커넥션 닫기 (이미 닫혔으면 무시)
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    # 카테고리별 상품 조회
    def get_items(self, category_id=None):
        if category_id is None:
            sql = "SELECT item_id, item_name, item_img FROM item;"
            self.cursor.execute(sql)
        else:
            sql = "SELECT item_id, item_name, item_img FROM item WHERE item_category = %s;"
            self.cursor.execute(sql, (category_id,))
        return self.cursor.fetchall()
    
    #
    def load_i_info(self, item_id) :
        """
        # 상품 item_id 에 따라 상세 정보를
        # TABLE item 에서 SELECT 합니다
        """
        sql = """
        SELECT i.* FROM item AS i
        WHERE
        %s = item_id
        """
        self.cursor.execute(sql, (item_id,))
        result = self.cursor.fetchone()
        self.close()
        return result
    
    # 타겟 유저 정보 조회
    def get_user_info(self, user_id: str):
        self.cur.execute("SELECT birth, gender FROM `user` WHERE user_id = %s", (user_id,))
        return self.cur.fetchone()

    # 나이(±2) + 성별 동일 유저 그룹 조회
    def get_homogeneous_users(self, gender: str, year: int, exclude_user: str):
        self.cur.execute("""
            SELECT u.user_id
            FROM `user` u
            WHERE u.gender = %s
              AND YEAR(u.birth) BETWEEN %s AND %s
              AND u.user_id != %s
        """, (gender, year-2, year+2, exclude_user))
        return [r[0] for r in self.cur.fetchall()]

    # 사용자 그룹의 구매 내역 조회 (상품 + 평점 + 리뷰수 + 이미지)
    def get_purchase_history_by_users(self, user_list: list[str]):
        if not user_list:
            return []
        format_strings = ','.join(['%s'] * len(user_list))
        sql = f"""
            SELECT ph.item_id, i.item_name, i.item_rate, i.item_reviewcnt, i.item_img
            FROM purchase_history ph
            JOIN item i ON ph.item_id = i.item_id
            WHERE ph.user_id IN ({format_strings})
        """
        self.cur.execute(sql, tuple(user_list))
        return self.cur.fetchall()

    # 특정 user의 구매 아이템 목록 조회
    def get_user_purchase_items(self, user_id: str):
        self.cur.execute("SELECT item_id FROM purchase_history WHERE user_id = %s", (user_id,))
        return {r[0] for r in self.cur.fetchall()}