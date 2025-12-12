"""
파일 이름 : woo_dao.py
파일 용도 :
 MVC 패턴에서 DB 와 상호작용 역할
작성 날짜 : 2025-11-25

"""
import pymysql
import pandas as pd

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

        # pandas_conn() 을 위한 밑작업
        self.dfconn = None
        self.dfcursor = None

    def pandas_conn(self) :
        """
        # pandas 의 data frame 을 쓰려할 때,
        # cursorclass 값이 default 가 아니면 문제발생
        # 함수가 호출될 때 DB 에 연결, dfcursor 생성
        """
        self.dfconn = pymysql.connect(
            #----- ----- ----- ----- ----- -----
            host="192.168.60.183",
            #host="localhost",
            #----- ----- ----- ----- ----- -----
            user="members",
            #user="root",
            #----- ----- ----- ----- ----- -----
            password="ezen",
            #----- ----- ----- ----- ----- -----
            database="shop"
            #database="local_shop"
            #----- ----- ----- ----- ----- -----
        )
        self.dfcursor = self.dfconn.cursor()

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# DB 와 상호작용 하는 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def main_banner(self, quantity = 1) :
        """
        # 전체상품 TALBE item 에서 각 대분류 별로
        # 역대 최고 평가 상품 item_id 을 반환 return
        """
        result = []
        for category_no in range(8) :
            ranking = self.calc_weighted_rate(option = 1, item_category = category_no)
            for quan in ranking[:quantity] :
                result.append(quan)

        self.close()
        return result

    def calc_ranking_item(self, quantity = 1, option = 0, category_no = 0) :
        """
        # 전체상품 TABLE item 에서
        # 역대 최고 평가 상위 quantity 개 까지 LIMIT quantity
        # 그리고 분류 Category 에서 소분류 item_category 로 대분류 parent_id
        # 조회 SELECT
        """
        ranking = self.calc_weighted_rate(option = option, item_category = category_no)

        result = []
        cate_li = []
        sql = """
        SELECT parent_id FROM category WHERE %s = category_id
        """
        for quan in ranking[:quantity] :
            result.append(quan)
            self.cursor.execute(sql, (quan["item_category"],))
            parent_no = self.cursor.fetchone()
            cate_li.append(parent_no['parent_id'])

        for quan in ranking[len(ranking) - quantity:] :
            result.append(quan)
            self.cursor.execute(sql, (quan["item_category"],))
            parent_no = self.cursor.fetchone()
            cate_li.append(parent_no['parent_id'])

        self.close()
        return result, cate_li


    def cate_rand_items(self, item_category) :
        """
        # 전체상품 TALBE item 의
        # 대분류 f(x)item_category 에서 "무작위" 상품 item_id 12개 까지 LIMIT 12
        """
        #, item_tag
        sql = """
        SELECT
            item_id, item_img, item_name, item_price
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
        # 전체상품 정보 TABLE item 에서 조회 SELECT
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
        # 장바구니 TALBE item_cart 에 추가 INSERT
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
    # """무한 스크롤""" by.sky
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    #상품 리스트 조회
    def get_items_by_parent(self, parent_id, offset, limit):
        """
        get_items_by_parent의 Docstring
        
        :param self: 설명
        :param parent_id: 설명
        :param offset: 설명
        :param limit: 설명
        """
        # 1) parent_id에서 소분류 목록 가져오기
        sql_sub = "select category_id from category where parent_id = %s"
        self.cursor.execute(sql_sub, (parent_id,))
        sub_categories = [row['category_id'] for row in self.cursor.fetchall()]

        if not sub_categories:
            return []  # 소분류 없으면 바로 return

        # 2) item 조회
        format_strings = ",".join(["%s"] * len(sub_categories))
        sql_items = f"""
            select item_id, item_name, item_price, item_img, item_category
            from item
            where item_category IN ({format_strings})
            order by item_id desc limit %s offset %s
        """
        params = sub_categories + [limit, offset]
        self.cursor.execute(sql_items, params)
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

    def pandas_close(self) :
        """
        # pd df type cursor 의 DB 연결 종료 함수
        """
        self.dfcursor.close()
        self.dfconn.close()

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 일반 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def calc_weighted_rate(self, option = 0, item_category = 0, values_array = None) :
        """
        # 별점과 리뷰수로 신뢰도를 추출해서
        # 신뢰성 높은 유의미한 별점을 추출하고
        # 신뢰성 별점을 기준으로 순위를 매기는 함수
        """

        # values_array 가 비어있는 경우 오류 방지
        if not values_array:
            #print("# " + "=" * 50)
            #print("Debug | File woo_dao | calc_weighted_rate() : !!! Array None !!!")
            #print("# " + "=" * 50)
            values_array = []
        placeholders = ', '.join(['%s'] * len(values_array))
        querys = [
        """
        SELECT
            item_id, item_name, item_rate, item_reviewcnt, item_img, item_category
        FROM
            item
        WHERE
            item_img IS NOT NULL
        """,
        f"""
        SELECT
            item_id, item_name, item_rate, item_reviewcnt, item_img, item_category
        FROM
            item 
        WHERE
            item_category BETWEEN {item_category} * 10 + 9 AND ({item_category} + 1) * 10 + 8
            AND item_img IS NOT NULL
        """,
        f"""
        SELECT
            item_id, item_name, item_price, item_rate, item_reviewcnt, item_img, item_category
        FROM
            item
        WHERE
            item_category IN ({placeholders}) AND item_img IS NOT NULL
        """
        ]
        try :
            self.pandas_conn()
            query = querys[option]
            df = pd.read_sql(query, self.dfconn)

            self.pandas_close()

        except Exception as e :
            print("# " + "=" * 50)
            print(f"데이터베이스 오류 발생: {e}")
            print("# " + "=" * 50)

            return []

        if df.empty :
            print("# " + "=" * 50)
            print("데이터프레임 오류 발생")
            print("# " + "=" * 50)

            return []

        df['item_rate'] = pd.to_numeric(df['item_rate'], errors='coerce')
        df['item_reviewcnt'] = pd.to_numeric(df['item_reviewcnt'], errors='coerce')

        # rate_mean : 전체 상품의 평균 별점
        rate_mean = df['item_rate'].mean()

        # m_vote (Minimum Votes): 순위에 진입하기 위한 최소 리뷰 수 기준
        # 여기서는 리뷰 수 분포의 상위 80% (Q80) 지점을 m_vote 으로 설정하여,
        # 리뷰 수가 충분히 많은 상품에 높은 가중치를 부여합니다.
        # m_vote = df['item_reviewcnt'].quantile(0.8) # 리뷰 수 상위 20%의 최소값
        # 또는 고정값 사용 (예: 50개)
        m_vote = m_vote = df['item_reviewcnt'].quantile(0.7)

        # 3. Weighted Rating (WR) 공식 적용
        def weighted_rating(row, m_vote, rate_mean):
            re_cnt = row['item_reviewcnt'] # v: 해당 상품의 리뷰 수
            s_rate = row['item_rate']     # R: 해당 상품의 별점

            # 분모가 0이 되는 경우를 방지하지만, 데이터 상 v와 m이 음수가 아닐 경우 안전합니다.
            if re_cnt + m_vote == 0:
                return 0.0

            val = (re_cnt / (re_cnt + m_vote) * s_rate) + (m_vote / (re_cnt + m_vote) * rate_mean)

            return val

        # DataFrame의 각 행에 공식 적용하여 'trust_score' 열 생성
        df['trust_score'] = df.apply(lambda row: weighted_rating(row, m_vote, rate_mean), axis=1)

        # 4. 'trust_score' 기준으로 내림차순 정렬
        df = df.sort_values(by='trust_score', ascending=False)

        # 5. 순위(Rank) 추가
        df['rank'] = range(1, len(df) + 1)

        # Flask 템플릿으로 넘기기 쉽도록 딕셔너리 리스트로 변환
        # 소수점 둘째 자리까지만 표시
        df['trust_score'] = df['trust_score'].round(2)

        return df.to_dict('records')
