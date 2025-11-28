import pymysql

class SkyDAO :
    def __init__(self) :
        self.conn = pymysql.connect(
            host="192.168.60.183",
            user="members",
            password="ezen",
            database="shop",
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()


    """장바구니"""
    #장바구니 - 상품 조회
    def cart_check(self, user_id) :
        try :
            #sql = "select * from item_cart where user_id = %s"
            sql = "select y.* from item_cart x inner join item y on x.item_id = y.item_id  where x.user_id = %s"
            self.cursor.execute(sql, (user_id,))
            cart_check = self.cursor.fetchall()
            return cart_check
        except Exception as e :
            self.conn.rollback()
            print(e)


    #장바구니 - 추천 상품 담기
    def item_add(self, user_id, item_id) :
        try :
            sql = "insert into item_cart(user_id, item_id) values(%s, %s)"
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
            sql = "insert into purchase_history(user_id, item_id) values(%s, %s)"
            self.cursor.execute(sql, (user_id, item_id))
            self.conn.commit()
        except Exception as e :
            self.conn.rollback()
            print(e)


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
        except Exception as e :
            self.conn.rollback()
            print(e)


    """구매내역"""
    #구매내역 - 상품 리스트
    def history_check(self, user_id) :
        try :
            sql = "select * from purchase_history where user_id = %s"
            self.cursor.execute(sql, (user_id,))
            history_check = self.cursor.fetchall()
            return history_check
        except Exception as e :
            self.conn.rollback()
            print(e)


    #데이터베이스 연결 종료
    def close(self) :
        self.cursor.close()
        self.conn.close()