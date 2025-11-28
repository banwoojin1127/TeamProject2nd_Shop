# import sys
# sys.path.append("D:\\Haneul\\Python\\project")

from flask import Blueprint, render_template, request, redirect, session, flash, Flask
from flask_dao.sky_dao import SkyDAO


#Flask 생성
app = Flask(__name__)
app.secret_key = "ezen"

#Blueprint 생성
sky_bp = Blueprint("sky", __name__)

#임시 저장된(session) user_id 값 가져오기
def get_user_id() :
    return session.get("user_id")

#item_id 값 가져오기
def get_item_id() :
    return session.get("item_id")

def get_item_name() :
    return session.get("item_name")


# ------------------------------
# 장바구니 - GET (화면)
# ------------------------------
@sky_bp.route("/cart", methods=["GET"])
def cart_page() :
    user_id = "excheck" #테스트 용 하드코딩
    #user_id = get_user_id()
    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 페이지입니다.")
        return redirect("/login")
    #장바구니 - 상품출력
    dao = SkyDAO()
    items = dao.cart_check(user_id)
    print(items)
    return render_template("sky/cart.html", datas=items)


# ------------------------------
# 장바구니 - POST (결제)
# ------------------------------
@sky_bp.route("/cart", methods=["POST"])
def payok() :
    user_id = "excheck" #테스트 용 하드코딩
    #user_id = get_user_id()

    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 페이지입니다.")
        return redirect("/login")

    #추천 상품 담기
    item_id = 1 #테스트 용 하드코딩
    #item_id = request.json["itemId"]
    dao = SkyDAO()
    dao.item_add(user_id, item_id)

    #장바구니에서 제거
    items_in_cart = dao.cart_check(user_id) #장바구니에 있는 상품
    remove = request.form.get("remove", False)
    if remove : 
        dao.item_remove(user_id, item_id)

    #결제
    for item in items_in_cart :
        item_id = item["id"]
        #결제 > 결제내역으로 추가
        if item_id :
            dao.item_pay(user_id, item_id)
        #결제 > 장바구니 초기화(비우기)
        dao.item_payok(user_id, item_id)
        return redirect("/cart")

# ------------------------------
# 결제내역 - GET (화면)
# ------------------------------
@sky_bp.route("/history", methods=["GET"])
def history_page() :
    user_id = 777 #테스트 용 하드코딩
    #user_id = request.args.get("user_id")
    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 페이지입니다.")
        return redirect("/login")
    return render_template("sky/history.html")


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
    return render_template("sky/search.html", items=items, keyword=keyword)


# ------------------------------
# 알고리즘 - GET (화면)
# ------------------------------
@sky_bp.route("/algo", methods=["GET"])
def algo_page() :
    return render_template("sky/algorithm.html")

"""
user_id = "excheck" #테스트 용 하드코딩
dao = SkyDAO()
items = dao.cart_check(user_id)
print(items)

"""