# # 검색 로그 긁어오는 코드

# from flask import Flask, request, render_template_string
# import logging

# # 1️⃣ 로그 설정
# logging.basicConfig(
#     filename="search.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s"
# )

# # 2️⃣ Flask 앱 생성
# app = Flask(__name__)

# # 3️⃣ HTML 템플릿 (임의의 더미 HTML)
# HTML_TEMPLATE = """
# <!doctype html>
# <html>
#   <head>
#     <title>Search Test</title>
#   </head>
#   <body>
#     <h1>검색 테스트</h1>
#     <form method="POST">
#       <input type="text" name="query" placeholder="검색어 입력">
#       <input type="submit" value="검색">
#     </form>
#     {% if results %}
#     <h2>결과</h2>
#     <ul>
#       {% for r in results %}
#       <li>{{ r }}</li>
#       {% endfor %}
#     </ul>
#     {% endif %}
#   </body>
# </html>
# """

# # 4️⃣ 라우팅
# @app.route("/searchlog", methods=["GET", "POST"])
# def search():
#     results = []
#     if request.method == "POST":
#         query = request.form.get("query")
#         logging.info(f"User searched: {query}")  # 로그 기록
#         results = [f"Dummy result for '{query}'"]  # 더미 결과
#     return render_template_string(HTML_TEMPLATE, results=results)

# # 5️⃣ 앱 실행
# if __name__ == "__main__":
#     app.run(debug=True)
