import pandas as pd
from sqlalchemy import create_engine

def add_rating(df):
    ratings_df=pd.read_csv('data/ratings.csv')
    ratings_df['movieId']=ratings_df['movieId'].astype(str)
    agg_df=ratings_df.groupby('movieId').agg(
        rating_count=('rating','count'),
        rating_avg=('rating','mean')
    ).reset_index()
    rating_added_df=df.merge(agg_df, on='movieId')
    return rating_added_df;

if __name__=="__main__":
    movies_df = pd.read_csv('data/movies.csv')
    movies_df['movieId']=movies_df['movieId'].astype(str)
    links_df=pd.read_csv('data/links.csv', dtype=str)
    merged_df = movies_df.merge(links_df, on='movieId', how='left')
    result_df = add_rating(merged_df)

    # SQLite 데이터베이스 엔진 생성
    engine = create_engine('sqlite:///data.db', echo=True)

    # 데이터프레임을 데이터베이스 테이블로 저장
    result_df.to_sql('movies', con=engine, if_exists='replace', index=False)