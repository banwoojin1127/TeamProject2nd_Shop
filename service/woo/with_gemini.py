"""
파일 이름 : with_gemini.py
작성일 : 2025-12-10
파일 용도 :
 API 용으로 DB 에서 Data 를 맞춤으로 조회하기 위함 

"""
import pymysql


class WithAPI :
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

    def for_recommend_cate_in_parent(self, user_id) :
        """
        # 1. 사용자 의 구매내역 을 조회
        # 2. 조회한 구매내역 의 상품 들을 대분류 로 그룹화하여 개수 조회
        # 3. 결과를 이하와 같이 return 할 것
        '사용자 구매내역 리스트' = 
            [
                { 대분류 : x, 분류명 : n, 구매수 : y },
                { 대분류 : x, 분류명 : n, 구매수 : y },
                { 대분류 : x, 분류명 : n, 구매수 : y },
                . . .
            ]
        # 4. !!! 이후 최종 결과가 만족스럽지 못하다면 대분류 -> 소분류 로 바꿀 것 
        """

        sql = """
            SELECT ph.item_id FROM purchase_history AS ph WHERE %s = ph.user_id
        """
        self.cursor.execute(sql, (user_id,))
        result = self.cursor.fetchall()

        purchase_tuple = tuple(item.get('item_id') for item in result)

        # purchase_tuple이 비어있는 경우(구매 이력 없음) 오류 방지
        if not purchase_tuple:
            print("구매 이력이 없어 처리할 항목이 없습니다.")
            return []

        placeholders = ', '.join(['%s'] * len(purchase_tuple))

        sql = f"""
            SELECT
                cg.parent_id AS main_category_id, 
                cg.category_name AS main_category_name, 
                COUNT(i.item_id) AS total_sales
            FROM
                item AS i
            INNER JOIN
                category AS cg ON i.item_category = cg.category_id
            WHERE
                i.item_id IN ({placeholders})
            GROUP BY
                cg.parent_id, cg.category_name
            ORDER BY
                main_category_id;
        """
        self.cursor.execute(sql, purchase_tuple)
        result = self.cursor.fetchall()

        self.close()
        return result


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
        # dict type cursor 의 DB 연결 종료 함수
        """
        self.cursor.close()
        self.conn.close()


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 일반 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
