import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform

from flask import current_app
from flask_dao.lsh_dao import LshDAO

def recommend_similarity(target: str, category_id=None, top_n=5):

    # DAO 생성 & 상품 데이터 조회
    dao = LshDAO()
    try:
        rows = dao.get_items(category_id)
    finally:
        dao.close()

    if not rows:
        print("DAO 조회 결과가 없음")
        return {"recommendations": []}

    # DataFrame 생성
    df = pd.DataFrame(rows).fillna("")
    df['item_name'] = df['item_name'].str.strip()

    # 텍스트 전처리
    def preprocess_name(text):
        text = re.sub(r"http\S+", " ", text)
        text = re.sub(r"\d+", " ", text)
        text = re.sub(r"[^가-힣a-zA-Z\s']", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    df['clean_name'] = df['item_name'].apply(preprocess_name)

    # TF-IDF 학습
    tfidf = TfidfVectorizer(ngram_range=(1, 2))
    matrix = tfidf.fit_transform(df['clean_name'])

    # 기준 상품 index 찾기
    row = df[df['item_name'] == target]
    if row.empty:
        print("기준 상품이 조회 결과에 없음")
        return {"recommendations": []}

    idx = row.index[0]

    # 유사도 계산 및 top 추천 추출
    sim = cosine_similarity(matrix[idx], matrix).flatten()
    s = pd.Series(sim, index=df.index)
    s = s.drop(idx)  # 자신 제외
    top = s.sort_values(ascending=False).head(top_n)

    # 결과 구성 (ID + 이미지)
    recommendations = [
        {"item_id": int(df.loc[i, "item_id"]), "item_img": df.loc[i, "item_img"]}
        for i in top.index
    ]
    
    # 한글 폰트 설정 (그래프)
    sys_name = platform.system()
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
    labels = [df.loc[i, "item_name"] for i in top.index]
    values = [s[i] for i in top.index]

    def shorten_label(label, max_len=10):
        return label if len(label) <= max_len else label[:max_len] + "..."

    short_labels = [shorten_label(l) for l in labels]

    plt.figure(figsize=(9, 5))
    plt.bar(short_labels, values)
    plt.title("추천 상품 유사도", fontsize=15)
    plt.ylabel("유사도", fontsize=12)
    plt.xticks(rotation=40, ha='right', fontsize=11)
    plt.tight_layout()
    plt.savefig("static/img/recommend_similarity_plot.png", dpi=300)  # static 폴더에 저장
    plt.close()  # 메모리 절약
    print("그래프 저장 완료")

    # Flask에서 사용 가능하도록 저장
    current_app.recommend_similarity_result = {
        "category_id": category_id,
        "target_item_id": int(df.loc[idx, "item_id"]),
        "recommendations": recommendations
    }

    return current_app.recommend_similarity_result
