from flask import Blueprint, render_template, session
from flask_dao.lsh_dao import LshDAO
from service.recommend_similarity import recommend_similarity
from service.recommend_user import recommend_user
from flask import current_app

lsh_bp = Blueprint('lsh', __name__)

parent_li = ["fruit", "veget", "meat", "seaf", "grnut", "bread", "snack", "bever"]

def cate_nav(category_no):
    session.pop("parent", None)
    if 0 <= category_no <= 7:
        parent = parent_li[category_no]
        session["parent"] = {parent: "class=active"}

@lsh_bp.route("/<int:category_no>/<int:item_no>")
@lsh_bp.route("/<int:category_no>/<int:item_no>/")
def item(category_no=0, item_no=0):
    # DAO 생성 및 사용
    dao = LshDAO()
    try:
        result = dao.load_i_info(item_no)
    finally:
        dao.close()

    # DB에서 조회한 category_no 사용
    db_category_no = result.get("item_category", category_no)  # 없으면 URL 값 사용
    cate_nav(db_category_no)

    # 세션에 저장
    session["cate_no"] = db_category_no
    session["item_no"] = item_no
    
    # 추천 실행
    try:
        recs = recommend_similarity(target=result["item_name"], category_id=db_category_no)
        recs = recs.get("recommendations", [])
    except Exception as e:
        print("추천 오류:", e)
        recs = []

    # 디버깅용 출력
    print("---- DEBUG ----")
    print("category_no:", category_no)
    print("item_no:", item_no)
    print("기준 상품 이름:", result.get("item_name"))
    print("추천 상품 리스트:", recs)
    print("----------------")

    return render_template("lsh/item.html", ie=result, recs=recs)

@lsh_bp.route("/mypage")
def mypage():
    user_id = session.get("user")
    dao = LshDAO()
    try:
        user = dao.get_user_info(user_id)
    finally:
        dao.close()

    if not user:
        return render_template("mypage.html", user=None, recs=[])

    # 추천 실행
    recommend_user(user_id)
    recs = current_app.recommend_user_result.get("recommendations", [])

    #디버깅용 출력
    print(f"유저 아이디: {user_id}")
    print(f"추천 상품 리스트: {recs}")

    return render_template("mypage.html", user=user, recs=recs)
