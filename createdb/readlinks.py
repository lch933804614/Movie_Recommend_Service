import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, MetaData, ForeignKey

# CSV 파일에서 데이터 읽기
csv_file = "./data/links.csv"
data = pd.read_csv(csv_file)

# 데이터베이스 연결 설정
db_uri = 'sqlite:///data.db'  # SQLite를 사용
engine = create_engine(db_uri)

# 테이블을 위한 메타데이터 생성
metadata = MetaData()

# links 테이블 생성
links = Table('links', metadata,
              Column('movieId', Integer, ForeignKey('movies.movieId'), primary_key=True),
              Column('imdbId', Integer),
              Column('tmdbId', Integer)
             )

# 데이터베이스에 테이블 생성
metadata.create_all(engine)

# 데이터프레임을 데이터베이스에 쓰기
data.to_sql('links', engine, if_exists='replace', index=False)

print("데이터베이스에 성공적으로 저장되었습니다.")