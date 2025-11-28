"""
파일 이름 : woo_dao.py
작성일 : 2025-11-25
파일 용도 :
 MVC 패턴에서 DB 와 상호작용 역할

"""
import pymysql

class WooDAO :
    """
    # DB 와 상호작용하는 기준 Class
    """
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# DB 와 연결하는 함수 (생성자)
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def __init__(self) :
        """
        # dao 클래스의 생성자
        # 생성자가 호출될 때 DB 에 연결, cursor 생성
        """
        self.conn = pymysql.connect(
            #----- ----- ----- ----- ----- -----
            host="192.168.60.183",
            #host="localhost",
            #----- ----- ----- ----- ----- -----
            user="members",
            #user="root",
            #----- ----- ----- ----- ----- -----
            password="ezen",
            #----- ----- ----- ----- ----- -----
            database="shop",
            #database="local_shop",
            #----- ----- ----- ----- ----- -----
            cursorclass=pymysql.cursors.DictCursor
            # 조회할 때만 : [(), ()] -> [{}, {}}]
        )
        self.cursor = self.conn.cursor()

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# DB 와 상호작용 하는 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def cate_rand_items(self, item_category) :
        """
        # item_category 내의 무작위 상품 item_id 12개
        """
        #, item_tag
        sql = """
        SELECT
            item_id, item_img
        FROM
            item
        WHERE
            item_category BETWEEN %s AND %s AND item_img IS NOT NULL
        ORDER BY
            RAND()
        LIMIT
            12
        """
        cate_s = item_category * 10 + 9
        cate_e = (item_category + 1) * 10 + 8
        self.cursor.execute(sql, (cate_s, cate_e))
        result = self.cursor.fetchall()
        self.close()
        return result


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


    def add_i_to_c(self, user_id, item_id) :
        """
        # 현재 상세를 보고있는 user_id 를 상품 item_id 와 묶어서
        # TALBE item_cart 에 INSERT 합니다
        """
        sql = """
        INSERT INTO item_cart
        (user_id, item_id)
        VALUES
        (%s, %s)
        """
        self.cursor.execute(sql, (user_id, item_id))
        self.conn.commit()
        # 쿼리가 실행됨으로 인해 영향을 받은 행의 개수
        cnt = self.cursor.rowcount
        self.close()
        return cnt

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# QED Temp 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def temp(self) :
        """
        # TEMP
        """
        sql = """
        DDL
        """
        self.cursor.execute(sql, (None,))
        #self.conn.commit()
        #result = self.cursor.fetchone()
        # 쿼리가 실행됨으로 인해 영향을 받은 행의 개수
        #cnt = self.cursor.rowcount
        self.close()
        return None

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# DB 와 연결을 종료하는 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def close(self) :
        """
        # DB 연결 종료 함수
        """
        self.cursor.close()
        self.conn.close()

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 일반 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
