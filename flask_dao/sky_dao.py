import pymysql
import traceback
from rapidfuzz import fuzz

class SkyDAO :
    def __init__(self) :
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


    """장바구니"""
    #장바구니 - 상품 조회
    def cart_check(self, user_id) :
        try :
            #sql = "select y.* from item_cart x inner join item y on x.item_id = y.item_id  where x.user_id = %s"
            sql = """
                SELECT i.item_id, i.item_name, i.item_price, i.item_rate, i.item_reviewcnt, i.item_img, i.item_category
                FROM item_cart c
                JOIN item i ON c.item_id = i.item_id
                WHERE c.user_id = %s
            """
            self.cursor.execute(sql, (user_id,))
            cart_check = self.cursor.fetchall()
            return cart_check
        except Exception as e :
            self.conn.rollback()
            return []

    #장바구니 - 추천 상품 조회
    def item_recommend(self) :
        try :
            #DB에서 단순 랜덤 추천
            sql = "select * from item order by rand() limit 3"
            
            #연관 상품 기반 추천
            #SELECT * FROM item WHERE item_category IN ( SELECT item_category FROM item_cart c JOIN item i ON c.item_id = i.item_id WHERE c.user_id = %s ) AND item_id NOT IN ( SELECT item_id FROM item_cart WHERE user_id = %s ) LIMIT 3;
            self.cursor.execute(sql)
            cart_check = self.cursor.fetchall()
            return cart_check
        except Exception as e :
            self.conn.rollback()
            return []

    #장바구니 - 추천 상품 담기
    def item_add(self, user_id, item_id) :
        try :
            sql = "INSERT INTO item_cart(user_id, item_id) VALUES (%s, %s)"
            self.cursor.execute(sql, (user_id, item_id))
            self.conn.commit()
        except Exception as e :
            self.conn.rollback()
            print(e)

    #장바구니 - 상품 제거
    def item_remove(self, user_id, item_id) :
        try :
            sql = "delete from item_cart WHERE user_id= %s and item_id= %s limit 1"
            self.cursor.execute(sql, (user_id, item_id))
            self.conn.commit()
        except Exception as e :
            self.conn.rollback()
            print(e)


    #장바구니 - 상품 결제 클릭 > 결제내역 추가
    def item_pay(self, user_id, item_id) :
        try :
            #item 테이블에서 이름/가격 가져오기
            sql = "select item_name, item_price from item where item_id = %s"
            self.cursor.execute(sql, (item_id,))
            item = self.cursor.fetchone()
            if not item :
                return None

            #purchase_history에 결제 상품 저장
            sql2 = "insert into purchase_history(user_id, item_id) values(%s, %s)"
            self.cursor.execute(sql2, (user_id, item_id))
            self.conn.commit()

        except Exception as e :
            self.conn.rollback()
            traceback.print_exc()
            return None
            #raise   # 예외를 다시 던져서 Flask에서 알 수 있게 함


    #장바구니 - 상품 결제 완료 > 장바구니 비우기
    def item_payok(self, user_id) :
        try :
            sql = "delete from item_cart where user_id = %s"
            self.cursor.execute(sql, (user_id,))
            self.conn.commit()
        except Exception as e :
            self.conn.rollback()
            print(e)

    """검색"""
    #상품 검색
    def item_search(self, item_name) :
        try :
            sql = "select * from item where item_name like %s"
            self.cursor.execute(sql, (f"%{item_name}%",))
            return self.cursor.fetchall()
        except Exception as e :
            self.conn.rollback()
            print(e)
            return []

    #검색 로그 수집(행위기반 로그)
    def save_search_log(self, user_id, keyword) :
        try :
            sql = "insert into search_log(user_id, keyword) values(%s, %s)"

            self.cursor.execute(sql, (user_id, keyword))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e :
            self.conn.rollback()
            print(e)
            return None
    
    #item_tag에서 태그 가져오기(DB에서 꺼내오기용)
    def get_item_tags(self, keyword):
        try :
            sql = "SELECT item_tag FROM item WHERE item_tag LIKE %s"
            self.cursor.execute(sql, ('%' + keyword + '%',))
            rows = self.cursor.fetchall()
            tags = []
            for row in rows:
                # item_tag가 여러 태그로 comma 구분되어 있다면 split
                tags.extend([t.strip() for t in row['item_tag'].split(',')])
            return tags
        except Exception as e :
            self.conn.rollback()
            print(e)
            return None
        
    #상품 item_tag 조회(출력)
    def get_item_tag(self, item_id) :
        try : 
            sql = "select item_tag from item where item_id = %s "
            self.cursor.execute(sql, (item_id,))
            row = self.cursor.fetchone()  # item_id 기준 하나만 가져오므로 fetchone
            if row and row['item_tag']:
                # 콤마로 구분된 태그를 리스트로 반환
                tags = [t.strip() for t in row['item_tag'].split(',')]
                return tags
            return []
        except Exception as e:
            print("get_item_tag error:", e)
            return []

    #검색 태그 수집(태그 등장 빈도 집계)
    def save_search_tag(self, keyword, tag) :
        try :
            sql = "insert into search_keyword_tag(keyword, tag) values(%s, %s) ON DUPLICATE KEY UPDATE tag_count = tag_count + 1"

            self.cursor.execute(sql, (keyword, tag))
            self.conn.commit()
        except Exception as e :
            self.conn.rollback()
            print(e)
            return None
        
    #검색 클릭 로그 수집
    def save_search_click(self, log_id, item_id) :
        try :
            sql = "insert into search_click_log(log_id, item_id) values(%s, %s)"
            
            self.cursor.execute(sql, (log_id, item_id))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e :
            self.conn.rollback()
            print(e)
            return None
        

    #RapidFuzz 유사도 기반 검색 필터
    def save_search_tag_fuzzy(self, keyword, threshold=70):
        """
        검색어(keyword)를 기준으로 item_tag에서 유사한 태그만 search_keyword_tag에 저장
        threshold: 유사도 기준 (0~100, 높을수록 stricter)
        """
        try:
            # 1. 모든 item 태그 조회
            sql = "SELECT item_tag FROM item"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()

            tags_set = set()
            for row in rows:
                if row['item_tag']:
                    for tag in row['item_tag'].split(','):
                        tag = tag.strip()
                        # keyword와 유사도가 threshold 이상이면 저장 대상
                        if fuzz.partial_ratio(keyword, tag) >= threshold:
                            tags_set.add(tag)

            # 2. search_keyword_tag 테이블에 저장 (중복 시 tag_count 증가)
            for tag in tags_set:
                sql_insert = """
                    INSERT INTO search_keyword_tag(keyword, tag)
                    VALUES(%s, %s)
                    ON DUPLICATE KEY UPDATE tag_count = tag_count + 1
                """
                self.cursor.execute(sql_insert, (keyword, tag))

            self.conn.commit()
            return list(tags_set)

        except Exception as e:
            self.conn.rollback()
            print("save_search_tag_fuzzy error:", e)
            return []


    """구매내역"""
    #구매내역 - 상품 리스트
    def history_check(self, user_id) :
        try :
            #sql = "select * from purchase_history where user_id = %s"

            sql = """
                    SELECT p.user_id, p.item_id, i.item_name, i.item_price, i.item_img, i.item_category FROM purchase_history p JOIN item i ON p.item_id = i.item_id WHERE p.user_id = %s order by p.purchase_id desc
                """
            self.cursor.execute(sql, (user_id,))
            history_check = self.cursor.fetchall()
            return history_check
        except Exception as e :
            self.conn.rollback()
            traceback.print_exc()
            return []
        
    """상품 상세보기"""
    #상품 상세보기 상품 아이디 조회
    def item_detail_by_id(self, item_id):
        try:
            sql = """
                SELECT *
                FROM item
                WHERE item_id = %s
            """
            self.cursor.execute(sql, (item_id,))
            return self.cursor.fetchone()
        except Exception:
            self.conn.rollback()
            traceback.print_exc()
            return None

    """순위"""
    


    #데이터베이스 연결 종료
    def close(self) :
        self.cursor.close()
        self.conn.close()