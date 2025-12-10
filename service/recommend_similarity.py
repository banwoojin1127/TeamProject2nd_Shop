import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import current_app
from flask_dao.lsh_dao import LshDAO

def recommend_similarity(target: str, category_id=None, top_n=5):

    # 캐시 초기화
    if not hasattr(current_app, "tfidf_cache"):
        current_app.tfidf_cache = {}

    cache = current_app.tfidf_cache

    # 캐시에 학습 데이터가 있는 경우 즉시 사용
    if category_id in cache:
        print("캐시된 TF-IDF 모델 사용")
        tfidf = cache[category_id]["vectorizer"]
        matrix = cache[category_id]["matrix"]
        df = cache[category_id]["df"]
    else:
        print("DAO 데이터로 새 TF-IDF 학습 실행")

        # DAO에서 상품 조회
        dao = LshDAO()
        try:
            rows = dao.get_items(category_id)
        finally:
            dao.close()

        if not rows:
            print("DAO 조회 결과 없음")
            return {"recommendations": []}

        # DataFrame 생성
        df = pd.DataFrame(rows).fillna("")
        df['item_name'] = df['item_name'].str.strip()

        # 전처리
        def preprocess_name(text):
            text = re.sub(r"http\S+", " ", text)
            text = re.sub(r"\d+", " ", text)
            text = re.sub(r"[^가-힣a-zA-Z\s']", " ", text)
            return re.sub(r"\s+", " ", text).strip()

        df['clean_name'] = df['item_name'].apply(preprocess_name)

        # TF-IDF 학습
        tfidf = TfidfVectorizer(
            ngram_range = (1, 3),   # 더 긴 n-gram 사용
            min_df = 1,
            max_df = 0.9
        )
        matrix = tfidf.fit_transform(df['clean_name'])

        # 학습된 데이터 캐싱
        cache[category_id] = {
            "vectorizer": tfidf,
            "matrix": matrix,
            "df": df
        }
        print("TF-IDF 모델 캐시에 저장 완료")

    # 기준 상품 찾기
    row = df[df['item_name'] == target]
    if row.empty:
        print("기준 상품 없음")
        return {"recommendations": []}

    idx = row.index[0]

    # 유사도 계산
    sim = cosine_similarity(matrix[idx], matrix).flatten()
    sim = sim ** 0.5    # 유사도 스케일 증가
    s = pd.Series(sim, index=df.index)

    # 자기 자신 제거
    s = s.drop(idx)

    # 유사도 1.0인 상품 제거
    s = s[s < 1.0]

    # 동일 유사도 값이 여러 개면 하나만 남기고 제거
    unique_s = s.groupby(s).head(1)

    # 유사도 높은 순서대로 정렬 후 top_n만 선택
    top = unique_s.sort_values(ascending=False).head(top_n)

    # 추천 상품 목록
    recommendations = [
        {
            "item_id": int(df.loc[i, "item_id"]),
            "item_name": df.loc[i, "item_name"],
            "item_img": df.loc[i, "item_img"],
            "similarity": float(s[i])
        }
        for i in top.index
    ]

    # Chart.js에서 사용할 그래프 데이터 구성
    graph_labels = [df.loc[i, "item_name"] for i in top.index]
    graph_values = [float(s[i]) for i in top.index]

    # Flask에서 사용할 데이터로 저장
    current_app.recommend_similarity_result = {
        "category_id": category_id,
        "target_item_id": int(df.loc[idx, "item_id"]),
        "recommendations": recommendations,
        "graph": {
            "labels": graph_labels,
            "values": graph_values
        }
    }

    return current_app.recommend_similarity_result
