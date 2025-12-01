import numpy as np
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform

from flask import current_app
from flask_dao.lsh_dao import LshDAO

def recommend_user(target_user: str, top_n=5):

    dao = LshDAO()

    # 유저 정보 가져오기
    row = dao.get_user_info(target_user)
    if not row:
        dao.close()
        return {"recommendations": [], "plot_img": None}

    birth, gender = row
    if not birth:
        dao.close()
        return {"recommendations": [], "plot_img": None}

    year = birth.year

    # 나이±2 + 성별 동일 유저 그룹
    user_group = dao.get_homogeneous_users(gender, year, target_user)

    # 없으면 전체 사용자로 대체 (본인 제외)
    if not user_group:
        all_users = dao.get_all_users_except(target_user)
        user_group = all_users

    # 그룹 구매 내역 조회 (이미지 포함)
    rows = dao.get_purchase_history_by_users(user_group)
    if not rows:
        dao.close()
        return {"recommendations": [], "plot_img": None}

    df = pd.DataFrame(rows, columns=["item_id", "item_name", "item_rate", "item_reviewcnt", "item_img"])
    df = df.fillna("")
    df["item_name"] = df["item_name"].str.strip()

    # 본인 구매 목록 set으로 가져오기
    my_items = dao.get_user_purchase_set(target_user)
    if not my_items:
        dao.close()
        return {"recommendations": [], "plot_img": None}

    # 유사도(Jaccard) 계산
    sim_scores = {}
    for uid in user_group:
        u_items = dao.get_user_purchase_set(uid)
        if not u_items:
            continue
        inter = len(my_items & u_items)
        union = len(my_items | u_items)
        sim_scores[uid] = inter / union if union else 0

    # 유사도 높은 유저 Top10 추출
    top_users = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    top_user_ids = [u for u, s in top_users]

    # 신규 추천 pool 구성
    pool = []
    for uid in top_user_ids:
        for iid in dao.get_user_purchase_set(uid):
            if iid not in my_items:
                pool.append(iid)

    if not pool:
        dao.close()
        return {"recommendations": [], "plot_img": None}

    # 많이 구매된 상품 Top5 item_id 추출
    freq = Counter(pool)
    rec_ids = [i for i, c in freq.most_common(top_n)]

    # 최종 추천 df 필터링 및 중복 제거
    recs = df[df["item_id"].isin(rec_ids)][["item_id", "item_name", "item_img"]]
    recs = recs.drop_duplicates("item_id").head(top_n)

    recommendations = [
        {"item_id": int(iid), "item_name": name, "item_img": img}
        for iid, name, img in recs.values
    ]

    # 한글 폰트 설정 (그래프)
    sys_name = platform.system()
    fp = None
    if sys_name == "Windows":
        fp = "C:/Windows/Fonts/malgun.ttf"
    elif sys_name == "Darwin":
        fp = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    else:
        found = [f for f in font_manager.findSystemFonts() if "Nanum" in f]
        fp = found[0] if found else None

    if fp:
        fprop = font_manager.FontProperties(fname=fp)
        rc('font', family=fprop.get_name())

    plt.rcParams['axes.unicode_minus'] = False

    # 추천 유사도 그래프 생성 & 저장
    labels = [r["item_name"] for r in recommendations]

    user_sets = {uid: dao.get_user_purchase_set(uid) for uid in top_user_ids}
    values = []
    for iid in rec_ids:
        sim_list = [sim_scores.get(uid, 0) for uid, uset in user_sets.items() if iid in uset]
        values.append(round(np.mean(sim_list) * 100, 2) if sim_list else 0)
    
    # 너무 길면 ... 처리
    short_labels = [l if len(l) <= 12 else l[:12] + "..." for l in labels]

    plt.figure(figsize=(9, 5))
    plt.bar(short_labels, values)
    plt.title(f"{target_user} - 유사 사용자 평균 유사도(%)", fontsize=15)
    plt.ylabel("유사도 평균 (%)", fontsize=12)
    plt.xticks(rotation=40, ha="right", fontsize=11)
    plt.tight_layout()
    plt.savefig("static/img/recommend_user_plot.png", dpi=300)
    plt.close()
    print("그래프 저장 완료")

    # Flask에서 사용 가능하도록 저장
    current_app.recommend_user_result = {
        "target_user": target_user,
        "recommendations": recommendations
    }

    return current_app.recommend_user_result