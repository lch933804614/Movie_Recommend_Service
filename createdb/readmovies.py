import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

# CSV 파일에서 데이터 읽기
csv_file = "./data/movies.csv"
data = pd.read_csv(csv_file)

# 데이터베이스 연결 설정
db_uri = 'sqlite:///data.db'  # SQLite를 사용
engine = create_engine(db_uri)

# 테이블을 위한 메타데이터 생성
metadata = MetaData()

# movies 테이블 생성
movies = Table('movies', metadata,
               Column('movieId', Integer, primary_key=True),
               Column('title', String),
               Column('genres', String)
              )

# 데이터베이스에 테이블 생성
metadata.create_all(engine)

# 데이터프레임을 데이터베이스에 쓰기
data.to_sql('movies', engine, if_exists='replace', index=False)

print("데이터베이스에 성공적으로 저장되었습니다.")