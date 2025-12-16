# import sys
# sys.path.append("D:\\Haneul\\Python\\project")

from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
import logging
from flask_dao.sky_dao import SkyDAO
from service.recommend_purchase import recommend_purchase

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 장바구니 - API 활용을 위한 import Start w.woo
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
from flask_dao.woo_dao import WooDAO
# woo = WooDAO()

from service.woo.for_gemini import WooGemini
wodel = WooGemini()
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 장바구니 - API 활용을 위한 import End w.woo
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

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

def get_user_id():
    user = session.get("user")  # session["user"]가 없으면 None 반환
    if user is None:
        return None
    return user.get("user_id")   # user가 dict이면 user_id 반환


# ------------------------------
# 장바구니 - GET (화면)
# ------------------------------
@sky_bp.route("/cart", methods=["GET"])
def cart_page() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()

    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 서비스입니다.") #메시지 등록
        return redirect(url_for("mhi.login_get"))
    
    #장바구니 - 상품출력
    user_id = get_user_id()
    dao = SkyDAO()
    items = dao.cart_check(user_id)

    for item in items:
        item['tags'] = dao.get_item_tag(item['item_id'])  # 기존 DAO 그대로 사용

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 장바구니 - API 를 활용한 추천 상품출력 Start w.woo
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    recommend_plan = None # sky.py 의 cart_page() 에서 그대로 웹으로 전달 할 것
    recommend_item = None # sky.py 의 cart_page() 에서 line:52 함수 반환값 대체 할 것
    user = session.get("user")
    if user :
        # WooGemini 및 WooDAO import 필수

        user_id = user.get("user_id")
# ===== API 한도 도달시 주석처리 하면 에러 회피 Start =====
#        recommend_plan = wodel.recommend_item_in_cart(user_id)
#        print("# " + "=" * 50 + "\n" + f"sky.py 추천API : {recommend_plan}" + "\n" + "# " + "=" * 50 + "\n")

#        dao = WooDAO()
#        recommend_item = dao.fetch_api_recommend_items(recommend_plan=recommend_plan, quantity=1)
# ===== API 한도 도달시 주석처리 하면 에러 회피 End =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 장바구니 - API 를 활용한 추천 상품출력 End w.woo
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    #장바구니 - 추천 상품출력
    recommend_items = recommend_item # 추천 상품 출력 w.woo
    #화면용 객체 저장
    session["recommend_items"] = recommend_items

    dao.close()
    return render_template("sky/cart.html", datas=items, rdatas=recommend_items
                           , recom_pl=recommend_plan) # 추천 알고리즘 플랜(recommend_plan) 추가 w.woo

# ------------------------------
# 장바구니 - POST (결제)
# ------------------------------
@sky_bp.route("/cart", methods=["POST"])
def payok() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()

    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 서비스입니다.") #메시지 등록
        return redirect(url_for("mhi.login_get"))
    
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
# 구매내역 - GET (화면)
# ------------------------------
@sky_bp.route("/history", methods=["GET"])
def history_page() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()
    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 서비스입니다.") #메시지 등록
        return redirect(url_for("mhi.login_get"))
    
    #구매 내역 출력
    dao = SkyDAO()
    items = dao.history_check(user_id)

    for item in items:
        item['tags'] = dao.get_item_tag(item['item_id'])  # 기존 DAO 그대로 사용

    dao.close()

    #추천 상품 출력
    rec_result = recommend_purchase(
        target_user=user_id,
        user_top_n=5,
        item_top_k=3
    )

    # 추천 실패 대비
    recommended_items = []
    chart_data = None
    similar_users = []

    if "error" not in rec_result:
        recommended_items = rec_result["recommended_items"]
        chart_data = rec_result["chart"]
        similar_users = rec_result["similar_users"]

    return render_template(
        "sky/history.html",
        datas=items,
        rdatas=recommended_items,
        chart=chart_data,
        similar_users=similar_users
    )

# ------------------------------
# 검색 - GET (화면, 검색결과 페이지)
# ------------------------------
@sky_bp.route("/search", methods=["GET"])
def search() :
    #검색
    keyword = request.args.get("keyword", "").strip()
    dao = SkyDAO()
    items = dao.item_search(keyword) if keyword else []

     # 최소 변경: 각 item에 'tags' 속성 추가
    for item in items:
        item['tags'] = dao.get_item_tag(item['item_id'])  # 기존 DAO 그대로 사용

    #검색 결과가 없으면 결과없음
    dao.close()
    return render_template(
    "sky/search.html",
    items=items,
    keyword=keyword,
    log_id=session.get("search_log_id")
)

# 검색 로그 설정
logging.basicConfig(
    filename="search.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# ------------------------------
# 검색 - POST (검색 로그 수집)
# ------------------------------
@sky_bp.route("/search", methods=["POST"])
def search_log():
    user_id = get_user_id()
    keyword = request.form.get("keyword", "").strip()
    items = []
    tags = []

    if user_id and keyword:
        dao = SkyDAO()
        
        # 1. 검색 로그 저장
        log_id = dao.save_search_log(user_id, keyword)
        session["search_log_id"] = log_id

        # 2. 검색 결과 가져오기
        items = dao.item_search(keyword)

        # 3. fuzzy 기반 유사 태그 저장
        tags = dao.save_search_tag_fuzzy(keyword, threshold=70)

        dao.close()

    # 4. 검색 결과 페이지 렌더링
    return render_template("sky/search.html", keyword=keyword, items=items, tags=tags)

# ------------------------------
# 상품 상세보기 GET
# ------------------------------

# ------------------------------
# 상품 상세보기 POST (클릭 로그 수집)
# ------------------------------
@sky_bp.route("/log/click", methods=["POST"])
def click_log():
    print("click_log() called..")

    log_id = session.get("search_log_id")  # 검색에서 온 경우 존재
    data = request.get_json()
    item_id = data.get("item_id")
    
    if not item_id:
        return "", 204

    dao = SkyDAO()
    
    # 검색 로그가 없으면 임시 로그 생성
    if not log_id:
        user_id = get_user_id()
        log_id = dao.save_search_log(user_id, keyword="")  # keyword 없으면 빈 문자열
        session["search_log_id"] = log_id

    dao.save_search_click(log_id, item_id)
    dao.close()
    return "", 204

# ------------------------------
# 상품 상세보기 - (화면)
# ------------------------------
# """
# @sky_bp.route("/<int:item_category>/<int:item_id>")
# def item_detail_page(item_category, item_id):
#     #print("item_category:" + str(item_category))
#     #print("item_id:" + str(item_id))

#     dao = SkyDAO()
#     item = dao.item_detail(item_category, item_id)
#     print(item)
#     return render_template("item.html", item=item)
# """
# ------------------------------
# 알고리즘 - GET (화면)
# ------------------------------
@sky_bp.route("/algo", methods=["GET"])
def algo_page() :
    #user_id = "lucky" #테스트 용 하드코딩
    user_id = get_user_id()
    #로그인 확인
    if not user_id :
        flash("로그인이 필요한 서비스입니다.") #메시지 등록
        return redirect(url_for("mhi.login_get"))
    return render_template("sky/algorithm.html")

# ------------------------------
# 랭킹 - GET (화면)
# ------------------------------
@sky_bp.route("/api/ranking")
def api_ranking():
    dao = SkyDAO()
    rows = dao.get_realtime_ranking()
    dao.close()
    return jsonify(rows)


"""
user_id = "excheck" #테스트 용 하드코딩
dao = SkyDAO()
items = dao.cart_check(user_id)
print(items)

"""