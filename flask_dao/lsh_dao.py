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

    # 전체 상품 조회
    def get_items_all(self):
        sql = """
            SELECT item_id, item_name, item_img, item_category 
            FROM item
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()

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
    
    # 유사 사용자 그룹이 가장 많이 구매한 상품 TOP 6 조회
    def get_top_items_from_users(self, user_list: list[str], top_n=6):
        """
        주어진 user_list의 구매 내역에서 가장 많이 구매된 상품 TOP N을 반환.
        item_id, item_name, item_img, item_category 포함.
        """
        if not user_list:
            return []

        format_strings = ','.join(['%s'] * len(user_list))

        sql = f"""
            SELECT 
                ph.item_id, 
                i.item_name,
                i.item_img, 
                i.item_category,
                COUNT(*) AS cnt
            FROM purchase_history ph
            JOIN item i ON ph.item_id = i.item_id
            WHERE ph.user_id IN ({format_strings})
            GROUP BY ph.item_id
            ORDER BY cnt DESC
            LIMIT %s;
        """

        params = tuple(user_list) + (top_n,)
        self.cursor.execute(sql, params)

        return self.cursor.fetchall()

    # 구매내역 전체 조회
    def get_purchase_history_all(self):
        sql = "SELECT user_id, item_id FROM purchase_history;"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    #전체 상품 조회 (이름만)
    def get_items_all_name(self):
        sql = "SELECT item_id, item_name FROM item"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        # DictCursor → tuple 변환
        return [(row["item_id"], row["item_name"]) for row in rows]
    
    # item_tag 저장
    def update_item_tag(self, item_id, tags):
        sql = "UPDATE item SET item_tag = %s WHERE item_id = %s"
        self.cursor.execute(sql, (tags, item_id))
        self.conn.commit()
