# import sys
# sys.path.append("D:\\Haneul\\Python\\project")

from flask import Blueprint, render_template, request, redirect, session, flash
from flask_dao.sky_dao import SkyDAO

#Blueprint 생성
sky_bp = Blueprint("sky", __name__)

#임시 저장된(session) user_id 값 가져오기
def get_user_id() :
    return session.get("user").get("user_id")

#item_id 값 가져오기
def get_item_id() :
    return session.get("item_id")

#item_name 값 가져오기
def get_item_name() :
    return session.get("item_name")

#item_price 값 가져오기 
def get_item_price() :
    return session.get("item_price")

# ------------------------------
# 장바구니 - GET (화면)
# ------------------------------
@sky_bp.route("/cart", methods=["GET"])
def cart_page() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()
    print(session.get("user"))

    #로그인 세션에 저장
    session["user_id"] = user_id

    #로그인 확인
    if not user_id :
        return redirect("/login")
    
    #장바구니 - 상품출력
    user_id = get_user_id()
    dao = SkyDAO()
    items = dao.cart_check(user_id)

    #장바구니 - 추천 상품출력
    recommend_items = dao.item_recommend()
    #화면용 객체 저장
    session["recommend_items"] = recommend_items 

    dao.close()
    return render_template("sky/cart.html", datas=items, rdatas=recommend_items)

# ------------------------------
# 장바구니 - POST (결제)
# ------------------------------
@sky_bp.route("/cart", methods=["POST"])
def payok() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()

    #로그인 확인
    if not user_id :
        return redirect("/login")
    
    dao = SkyDAO()

    #장바구니 목록 가져오기
    items_in_cart = dao.cart_check(user_id)

    #결제처리
    paid_items = []
    for item in items_in_cart :
        obj = dao.item_pay(user_id, item["item_id"])
        #결제 > 결제내역으로 추가
        if obj :
            paid_items.append(obj)
                #item["item_name"],
                #item["item_price"]
    #결제완료 > 장바구니 초기화(비우기)
    dao.item_payok(user_id)
    #session["키"] = 값
    dao.close()
    #화면용 객체 저장
    session["paid_items"] = paid_items 
    return redirect("/history")

#추천 상품 담기
@sky_bp.route("/cart/add/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    user_id = get_user_id()
    #user_id = "lucky" #테스트 용 하드코딩
    #item_id = request.json["itemId"]
    #item_id = 17956 #테스트 용 하드코딩
    dao = SkyDAO()
    dao.item_add(user_id, item_id)
    dao.close()
    return redirect("/cart")
    
#장바구니에서 제거
@sky_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id):
    #user_id = "lucky"
    user_id = get_user_id()
    dao = SkyDAO()
    dao.item_remove(user_id, item_id)
    dao.close()
    return redirect("/cart")

# ------------------------------
# 결제내역 - GET (화면)
# ------------------------------
@sky_bp.route("/history", methods=["GET"])
def history_page() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()
    #로그인 확인
    if not user_id :
        return redirect("/login")
    
    #결제 내역 출력
    dao = SkyDAO()
    items = dao.history_check(user_id)
    dao.close()
    return render_template("sky/history.html", datas=items)

# ------------------------------
# 검색 - GET (화면, 검색결과)
# ------------------------------
@sky_bp.route("/search", methods=["GET"])
def search() :
    #검색
    keyword = request.args.get("keyword", "").strip()
    dao = SkyDAO()
    items = dao.item_search(keyword) if keyword else []
    #검색 결과가 없으면 결과없음
    dao.close()
    return render_template("sky/search.html", items=items, keyword=keyword)

# ------------------------------
# 상품 상세보기 - (화면)
# ------------------------------
"""
@sky_bp.route("/<int:item_category>/<int:item_id>")
def item_detail_page(item_category, item_id):
    #print("item_category:" + str(item_category))
    #print("item_id:" + str(item_id))

    dao = SkyDAO()
    item = dao.item_detail(item_category, item_id)
    print(item)
    return render_template("item.html", item=item)
"""
# ------------------------------
# 알고리즘 - GET (화면)
# ------------------------------
@sky_bp.route("/algo", methods=["GET"])
def algo_page() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()
    #로그인 확인
    if not user_id :
        return redirect("/login")
    return render_template("sky/algorithm.html")

"""
user_id = "excheck" #테스트 용 하드코딩
dao = SkyDAO()
items = dao.cart_check(user_id)
print(items)

"""