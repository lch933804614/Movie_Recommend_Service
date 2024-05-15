import pandas as pd

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
    print(result_df)
