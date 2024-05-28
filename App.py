import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QLineEdit, 
                             QMessageBox, QPushButton, QCheckBox, QHBoxLayout, QLabel, QDoubleSpinBox, 
                             QTabWidget, QDialog, QDialogButtonBox, QListWidget)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData
import requests
import tmdbsimple as tmdb
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

# TMDb API 키 설정
tmdb.API_KEY = 'ef1218269ce140d0b05e4f622f7fcd02'

def fetch_movie_poster_from_tmdb(movie_id):
    movie = tmdb.Movies(movie_id)
    response = movie.info()
    poster_path = response.get('poster_path')
    if poster_path:
        poster_url = f'https://image.tmdb.org/t/p/original{poster_path}'
        return poster_url
    else:
        return None

class MovieDetailDialog(QDialog):
    def __init__(self, title, genres, tags, poster_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Movie Info")
        self.setFixedSize(500, 600)  # 고정된 크기로 설정
        
        layout = QVBoxLayout()
        
        # 영화 제목
        title_label = QLabel(f"<b>Title:</b> {title}")
        layout.addWidget(title_label)
        
        # 영화 장르
        genres_label = QLabel(f"<b>Genres:</b> {genres}")
        layout.addWidget(genres_label)
        
        # 영화 태그
        tags_label = QLabel(f"<b>Tags:</b> {tags}")
        layout.addWidget(tags_label)
        
        # 영화 포스터
        if poster_url:
            response = requests.get(poster_url)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            scaled_pixmap = pixmap.scaledToWidth(300)  # 가로 너비를 300으로 조절
            poster_label = QLabel()
            poster_label.setPixmap(scaled_pixmap)
            layout.addWidget(poster_label)
        
        self.setLayout(layout)

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Movie RC System')
        self.setWindowIcon(QIcon('ClapperBoardIcon.png'))
        self.setGeometry(450, 150, 1000, 800)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()

        # 영화 리스트 탭
        self.movie_tab = QWidget()
        self.initMovieTab()

        # 영화 추천 탭
        self.recommendation_tab = QWidget()
        self.initRecommendationTab()

        # 탭 위젯에 탭 추가
        self.tab_widget.addTab(self.movie_tab, "영화 리스트")
        self.tab_widget.addTab(self.recommendation_tab, "영화 추천")

        # 수직 레이아웃 생성 및 탭 위젯 추가
        vbox = QVBoxLayout()
        vbox.addWidget(self.tab_widget)
        self.setLayout(vbox)
        self.show()
        
    def initMovieTab(self):

        # 데이터베이스 연결 설정
        db_uri = 'sqlite:///data.db'
        engine = create_engine(db_uri)
        metadata = MetaData()

        # movies 테이블에 연결
        movies = Table('movies', metadata,
                       Column('movieId', Integer, primary_key=True),
                       Column('title', String),
                       Column('genres', String),
                       Column('rating_avg', Float)  # rating_avg 열 추가
                      )
        
        # 데이터베이스와 연결하고 movies 테이블에서 데이터 가져오기
        with engine.connect() as conn:
            query = conn.execute(movies.select())
            movies_list = query.fetchall()

        # 영화 리스트를 표시할 QTableWidget 생성
        self.movie_table_widget = QTableWidget()
        self.movie_table_widget.setColumnCount(3)  # 열의 개수 설정
        self.movie_table_widget.setHorizontalHeaderLabels(['Title', 'Genres', 'Avg Rating'])  # 열 제목 설정
        self.movie_table_widget.setColumnWidth(0, 400) # 1열 너비 지정
        self.movie_table_widget.setColumnWidth(1, 400) # 2열 너비 지정
        self.movie_table_widget.setColumnWidth(2, 200) # 3열 너비 지정

        # 영화 리스트를 표에 추가
        for row, movie in enumerate(movies_list):
            title = movie[1]
            genres = movie[2]
            rating_avg = str(round(movie[3], 2)) if movie[3] is not None else ''  # 소수점 둘째 자리에서 반올림, 평점 평균이 없으면 빈 문자열

            self.movie_table_widget.insertRow(row)

            # 제목 셀 설정 (읽기 전용으로 설정)
            title_item = QTableWidgetItem(title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)  # 편집 불가능하도록 설정
            self.movie_table_widget.setItem(row, 0, title_item)

            # 장르 셀 설정 (읽기 전용으로 설정)
            genres_item = QTableWidgetItem(genres)
            genres_item.setFlags(genres_item.flags() & ~Qt.ItemIsEditable)  # 편집 불가능하도록 설정
            self.movie_table_widget.setItem(row, 1, genres_item)

            # 평균 평점 셀 설정 (읽기 전용으로 설정)
            rating_avg_item = QTableWidgetItem(rating_avg)
            rating_avg_item.setFlags(rating_avg_item.flags() & ~Qt.ItemIsEditable)  # 편집 불가능하도록 설정
            self.movie_table_widget.setItem(row, 2, rating_avg_item)

        # 영화 테이블의 아이템 클릭 시 상세 정보 표시
        self.movie_table_widget.itemClicked.connect(self.show_movie_detail)
        
        # 검색 상자 추가
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("제목을 입력하세요.")
        self.search_box.textChanged.connect(self.filter_table)

        # "전체" 체크박스 추가
        self.all_checkbox = QCheckBox("전체")
        self.all_checkbox.setChecked(True)  # 기본적으로 선택되도록 설정
        self.all_checkbox.stateChanged.connect(self.toggle_all_genres)
        self.all_checkbox.stateChanged.connect(self.filter_table)
        

        # 장르 선택 체크박스 추가
        self.genre_checkboxes = []
        self.genre_layout = QHBoxLayout()
        for genre in [
            'Action', 'Adventure', 'Animation', "Children", 'Comedy', 'Crime',
            'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
            'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'
        ]:
            checkbox = QCheckBox(genre)
            checkbox.stateChanged.connect(self.filter_table)
            checkbox.stateChanged.connect(self.check_genre_checkbox)
            self.genre_checkboxes.append(checkbox)
            self.genre_layout.addWidget(checkbox)
                    
        # 평점 범위 입력 상자 추가
        self.rating_checkbox = QCheckBox('평점 검색')
        self.rating_checkbox.stateChanged.connect(self.toggle_rating)
        self.rating_checkbox.stateChanged.connect(self.filter_table)
        self.min_rating_box = QDoubleSpinBox()
        self.max_rating_box = QDoubleSpinBox()
        self.min_rating_box.setRange(1.0, 5.0)
        self.min_rating_box.setEnabled(False)
        self.max_rating_box.setRange(1.0, 5.0)
        self.max_rating_box.setEnabled(False)
        self.min_rating_box.setSingleStep(0.01)
        self.max_rating_box.setSingleStep(0.01)
        self.min_rating_box.setValue(1.0)
        self.max_rating_box.setValue(5.0)
        from_label = QLabel("에서")
        to_label = QLabel("까지")
        self.min_rating_box.textChanged.connect(self.filter_table)
        self.max_rating_box.textChanged.connect(self.filter_table)

        # 수평 레이아웃 생성
        hbox = QHBoxLayout()
        hbox.addWidget(self.rating_checkbox)
        hbox.addWidget(self.min_rating_box)
        hbox.addWidget(from_label)
        hbox.addWidget(self.max_rating_box)
        hbox.addWidget(to_label)
        hbox.addStretch(1)

        # 수직 레이아웃 생성
        vbox = QVBoxLayout() 
        vbox.addWidget(self.search_box)
        vbox.addWidget(self.all_checkbox)
        vbox.addLayout(self.genre_layout)
        vbox.addLayout(hbox)
        vbox.addWidget(self.movie_table_widget)

        self.movie_tab.setLayout(vbox)

    def toggle_rating(self, state):
        # 평점 검색 체크박스가 선택된 경우 평점 검색을 활성화
        self.min_rating_box.setEnabled(state == Qt.Checked)
        self.max_rating_box.setEnabled(state == Qt.Checked)

    def toggle_all_genres(self, state):
        # "전체" 체크박스가 선택된 경우 다른 체크박스들의 체크를 해제
        if state == Qt.Checked:
            for checkbox in self.genre_checkboxes:
                checkbox.setChecked(False)
        self.filter_table()

    def check_genre_checkbox(self):
        # 다른 장르 체크박스가 선택된 경우 "전체" 체크박스의 체크를 해제
        if any(checkbox.isChecked() for checkbox in self.genre_checkboxes):
            self.all_checkbox.setChecked(False)
        self.filter_table()

    def filter_table(self):
        search_text = self.search_box.text().lower()
        selected_genres_all = self.all_checkbox.isChecked()
        selected_genres = [checkbox.text().lower() for checkbox in self.genre_checkboxes if checkbox.isChecked()]
        ratingsearch_enabled = self.rating_checkbox.isChecked()
        min_rating = float(self.min_rating_box.text()) if self.min_rating_box.text() else 0.0
        max_rating = float(self.max_rating_box.text()) if self.max_rating_box.text() else float('inf')
        for row in range(self.movie_table_widget.rowCount()):
            title = self.movie_table_widget.item(row, 0).text().lower()
            genres = self.movie_table_widget.item(row, 1).text().lower()
            rating_avg = float(self.movie_table_widget.item(row, 2).text()) if self.movie_table_widget.item(row, 2) else 0.0
            if (
                search_text in title and 
                (self.all_checkbox.isChecked() or all(genre in genres.split('|') for genre in selected_genres)) and
                (not self.rating_checkbox.isChecked() or min_rating <= rating_avg <= max_rating)
            ):
                self.movie_table_widget.setRowHidden(row, False)
            else:
                self.movie_table_widget.setRowHidden(row, True) 

    # 영화정보 불러오기
    def get_movie_info_from_database(self, movie_title):
        db_uri = 'sqlite:///data.db'
        engine = create_engine(db_uri)
        metadata = MetaData()
        movies = Table('movies', metadata, autoload_with=engine)
        with engine.connect() as conn:
            query = movies.select().where(movies.c.title == movie_title)
            movie = conn.execute(query).fetchone()
        if movie:
            return movie[1], movie[2], movie[0]  # title, genres, movieId
        return None, None, None

    # 태그 정보 불러오는 메소드
    def get_movie_tags_from_database(self, movie_id):
        db_uri = 'sqlite:///data.db'
        engine = create_engine(db_uri)
        metadata = MetaData()
        tags = Table('tags', metadata,
                     Column('userId', Integer),
                     Column('movieId', Integer),
                     Column('tag', String),
                     Column('timestamp', Integer)
                    )
        with engine.connect() as conn:
            query = tags.select().where(tags.c.movieId == movie_id)
            tags_list = conn.execute(query).fetchall()
        return [tag[2] for tag in tags_list]
    
    def show_movie_detail(self, item):
        row = item.row()
        movie_title = self.movie_table_widget.item(row, 0).text()
        db_uri = 'sqlite:///data.db'
        engine = create_engine(db_uri)
        metadata = MetaData()
        movies = Table('movies', metadata, autoload_with=engine)
        links = Table('links', metadata, autoload_with=engine)
        with engine.connect() as conn:
            query = movies.select().where(movies.c.title == movie_title)
            movie = conn.execute(query).fetchone()
            if movie:
                movie_id = movie[0]
                tmdb_id_query = links.select().where(links.c.movieId == movie_id)
                tmdb_id_result = conn.execute(tmdb_id_query).fetchone()
                if tmdb_id_result:
                    tmdb_id = tmdb_id_result[2]
                    movie_genres = movie[2]
                    movie_tags = self.get_movie_tags_from_database(movie_id)
                    tags_text = ', '.join(movie_tags) if movie_tags else 'No tags available'
                    
                    # TMDb API를 사용하여 영화 포스터를 가져옵니다.
                    poster_url = fetch_movie_poster_from_tmdb(tmdb_id)
                    
                    # 영화 상세 정보 다이얼로그 표시
                    dialog = MovieDetailDialog(movie_title, movie_genres, tags_text, poster_url, parent=self)
                    dialog.exec_()
                else:
                    QMessageBox.information(self, "Movie Info", f"No TMDB ID found for {movie_title}")
            else:
                QMessageBox.information(self, "Movie Info", f"No details found for {movie_title}")
    
    # 영화 추천 탭 초기화 메서드
    def initRecommendationTab(self):
        # 영화 추천 탭 초기화 메서드
        # 선택된 영화를 저장할 리스트
        self.selected_movies = []

        # 선택된 장르를 저장할 리스트
        self.selected_genres = []

        # 장르 선택 체크박스 추가
        self.genre_checkboxes_rec = []
        self.genre_layout_rec = QHBoxLayout()
        for genre in [
            'Action', 'Adventure', 'Animation', "Children", 'Comedy', 'Crime',
            'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
            'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'
        ]:
            checkbox = QCheckBox(genre)
            checkbox.stateChanged.connect(self.update_selected_genres)
            self.genre_checkboxes_rec.append(checkbox)
            self.genre_layout_rec.addWidget(checkbox)

        # 선택된 영화를 표시할 QTableWidget 추가
        self.selected_movies_table = QTableWidget()
        self.selected_movies_table.setColumnCount(2)
        self.selected_movies_table.setHorizontalHeaderLabels(['Title', 'Remove'])
        self.selected_movies_table.setColumnWidth(0, 600)  # 제목 열 너비 지정
        self.selected_movies_table.setColumnWidth(1, 100)  # 삭제 버튼 열 너비 지정

        # 영화 선택 버튼 추가
        select_movie_button = QPushButton('영화 선택')
        select_movie_button.clicked.connect(self.select_movie_from_list)

        # 영화 추천 버튼 추가
        recommend_button = QPushButton('영화 추천')
        recommend_button.clicked.connect(self.recommend_movie)

        # 수직 레이아웃 생성
        vbox = QVBoxLayout()
        vbox.addLayout(self.genre_layout_rec)
        vbox.addWidget(select_movie_button)
        vbox.addWidget(self.selected_movies_table)
        vbox.addWidget(recommend_button)
        
        self.recommendation_tab.setLayout(vbox)
    
    # 선택된 장르 업데이트 메서드
    def update_selected_genres(self):
        self.selected_genres = [cb.text() for cb in self.genre_checkboxes_rec if cb.isChecked()]
    
    # 영화 선택 메서드
    def select_movie_from_list(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('영화 선택')

        layout = QVBoxLayout()

        # 검색어 입력을 위한 QLineEdit 추가
        search_box = QLineEdit()
        search_box.setPlaceholderText('검색어를 입력하세요...')
        layout.addWidget(search_box)

        list_widget = QListWidget()
        for row in range(self.movie_table_widget.rowCount()):
            title = self.movie_table_widget.item(row, 0).text()
            list_widget.addItem(title)
        
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        buttons.accepted.connect(lambda: self.add_selected_movie(list_widget, dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        # 검색어 변경 시 호출될 함수 정의
        def filter_movies():
            search_text = search_box.text().lower()
            for row in range(list_widget.count()):
                item = list_widget.item(row)
                item.setHidden(search_text not in item.text().lower())
        
        # 검색어 변경 시 filter_movies 함수 호출
        search_box.textChanged.connect(filter_movies)

        dialog.exec_()
    
    def add_selected_movie(self, list_widget, dialog):
        selected_movie = list_widget.currentItem().text()
        if selected_movie and selected_movie not in self.selected_movies:
            self.selected_movies.append(selected_movie)
            self.update_selected_movies_display()
        dialog.accept()

    # 선택된 영화 표시 업데이트 메서드
    def update_selected_movies_display(self):
        self.selected_movies_table.setRowCount(0)
        for i, movie in enumerate(self.selected_movies):
            self.selected_movies_table.insertRow(i)
            self.selected_movies_table.setItem(i, 0, QTableWidgetItem(movie))
            remove_button = QPushButton('Remove')
            remove_button.clicked.connect(lambda _, m=movie: self.remove_selected_movie(m))
            self.selected_movies_table.setCellWidget(i, 1, remove_button)

    # 선택된 영화 제거 메서드
    def remove_selected_movie(self, movie):
        if movie in self.selected_movies:
            self.selected_movies.remove(movie)
            self.update_selected_movies_display()
    
    # 영화 추천 메서드
    def recommend_movie(self):
        if self.selected_movies:
            # 선택된 영화의 장르를 벡터화
            selected_movies_genres = []
            for movie in self.selected_movies:
                for row in range(self.movie_table_widget.rowCount()):
                    title = self.movie_table_widget.item(row, 0).text().lower()
                    genres = self.movie_table_widget.item(row, 1).text().lower()
                    if movie.lower() == title:
                        selected_movies_genres.append(genres)
                        break
            
            # 선택된 장르 필터링
            if self.selected_genres:
                selected_genres_set = set(genre.lower() for genre in self.selected_genres)
                filtered_movies_genres = []
                filtered_movie_titles = []
                for row in range(self.movie_table_widget.rowCount()):
                    title = self.movie_table_widget.item(row, 0).text()
                    genres = self.movie_table_widget.item(row, 1).text().lower()
                    if selected_genres_set.intersection(set(genres.split('|'))):
                        filtered_movies_genres.append(genres)
                        filtered_movie_titles.append(title)
            else:
                filtered_movies_genres = []
                filtered_movie_titles = []

            # CountVectorizer를 사용하여 장르 벡터화
            vectorizer = CountVectorizer(tokenizer=lambda x: x.split('|'), token_pattern=None)
            genre_matrix = vectorizer.fit_transform(filtered_movies_genres)
            
            # 선택된 영화의 장르 벡터 생성
            selected_movies_matrix = vectorizer.transform(selected_movies_genres)
            
            # 코사인 유사도 계산
            cosine_sim = cosine_similarity(selected_movies_matrix, genre_matrix)
            
            # 선택된 영화와 가장 유사한 영화 찾기
            avg_cosine_sim = cosine_sim.mean(axis=0)
            most_similar_idx = avg_cosine_sim.argmax()
            
            most_similar_movie = filtered_movie_titles[most_similar_idx] if filtered_movie_titles else "없음"
            
            QMessageBox.information(self, "영화 추천", f"추천된 영화: {most_similar_movie}")
        else:
            QMessageBox.information(self, "영화 추천", "선택된 영화가 없습니다.")
    
    # 영화 추천 페이지로 이동하는 메서드
    def go_to_recommendation(self):
        self.tab_widget.setCurrentIndex(1)  # 영화 추천 탭의 인덱스는 1이므로 해당 탭으로 이동

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())