"""
파일 이름 : app.py
작성일 : 2025-11-25
파일 용도 :
 Python 의 Flask 실행 기준점이 되는 파일
 라우터 파일들을 임포트 받음으로서 묶어주는 역할

"""
from flask import Flask

# 분리된 라우터 파일 임포트
from routes.woo import woo_bp
from routes.sky import sky_bp
from routes.mhi import mhi
from routes.lsh import lsh_bp



app = Flask(__name__)
app.secret_key = "ezen"

# 분리된 woo 라우터를 flask 에 등록
app.register_blueprint(woo_bp)
app.register_blueprint(sky_bp)
app.register_blueprint(mhi)
app.register_blueprint(lsh_bp)


# 디버그 모드로 Flask 실행
# 디버그 모드 : .py 나 .html 등등이 변경되었을때,
# 서버를 재시작 할 필요 없이 변경 사항이 반영됨
app.run(debug=True)
