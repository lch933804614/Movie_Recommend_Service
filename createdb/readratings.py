import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, Float, Date, MetaData

# CSV 파일에서 데이터 읽기
csv_file = "./data/ratings.csv"
data = pd.read_csv(csv_file)

# timestamp를 datetime 형식으로 변환하고 날짜 정보만 추출
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s').dt.date

# 데이터베이스 연결 설정
db_uri = 'sqlite:///data.db'  # SQLite를 사용
engine = create_engine(db_uri)

# 테이블을 위한 메타데이터 생성
metadata = MetaData()

# ratings 테이블 생성
movies = Table('tags', metadata,
               Column('userId', Integer, primary_key=True),
               Column('movieId', Integer),
               Column('rating', Float),
               Column('timestamp', Date)
              )

# 데이터베이스에 테이블 생성
metadata.create_all(engine)

# 데이터프레임을 데이터베이스에 쓰기
data.to_sql('ratings', engine, if_exists='replace', index=False)

print("데이터베이스에 성공적으로 저장되었습니다.")