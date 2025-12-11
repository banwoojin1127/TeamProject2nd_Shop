import pymysql
import traceback
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
    #상품 상세보기 조회
    def item_detail(self, item_category, item_id) :
        try :
            sql = """
                select * from item where item_category = %s and item_id = %s
            """
            self.cursor.execute(sql, (item_category, item_id))
            result = self.cursor.fetchone()
            return result
        except Exception as e :
            self.conn.rollback()
            traceback.print_exc()
            return []

    #데이터베이스 연결 종료
    def close(self) :
        self.cursor.close()
        self.conn.close()