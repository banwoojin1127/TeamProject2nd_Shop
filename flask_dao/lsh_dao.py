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

    # 전체 상품 조회 (이름만)
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

    # 기간별 구매내역 조회
    def get_purchase_history_all_by_period(self, period):
        if period == "daily":
            condition = "purchase_date >= CURDATE()"
        elif period == "weekly":
            condition = "purchase_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif period == "monthly":
            condition = "purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
        else:
            condition = "1=1"

        sql = f"""
            SELECT user_id, item_id
            FROM purchase_history
            WHERE {condition}
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
        
    # 기간 + 유사 사용자 기준 TOP 상품
    def get_top_items_from_users_by_period(self, user_ids, period, top_n=6):
        if not user_ids:
            return []

        if period == "daily":
            condition = "p.purchase_date >= CURDATE()"
        elif period == "weekly":
            condition = "p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif period == "monthly":
            condition = "p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
        else:
            condition = "1=1"

        placeholders = ",".join(["%s"] * len(user_ids))

        sql = f"""
            SELECT
                i.item_id,
                i.item_name,
                i.item_price,
                i.item_category,
                i.item_img,
                COUNT(*) AS cnt
            FROM purchase_history p
            JOIN item i ON p.item_id = i.item_id
            WHERE p.user_id IN ({placeholders})
            AND {condition}
            GROUP BY i.item_id
            ORDER BY cnt DESC
            LIMIT %s
        """

        params = user_ids + [top_n]

        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
