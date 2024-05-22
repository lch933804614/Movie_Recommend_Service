import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QLineEdit, 
                             QMessageBox, QPushButton, QCheckBox, QHBoxLayout, QLabel, QDoubleSpinBox, 
                             QTabWidget, QDialog, QDialogButtonBox, QListWidget)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

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
        # 영화 리스트 탭 초기화 메서드
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
            'Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime',
            'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
            'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'
        ]:
            checkbox = QCheckBox(genre)
            checkbox.stateChanged.connect(self.filter_table)
            checkbox.setEnabled(False)
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
        self.min_rating_box.valueChanged.connect(self.filter_table)
        self.max_rating_box.valueChanged.connect(self.filter_table)

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
            'Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime',
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

    def filter_table(self):
        search_text = self.search_box.text().lower()
        selected_genres = {cb.text() for cb in self.genre_checkboxes if cb.isChecked()}
        min_rating = self.min_rating_box.value()
        max_rating = self.max_rating_box.value()
        filter_by_rating = self.rating_checkbox.isChecked()

        for row in range(self.movie_table_widget.rowCount()):
            title_item = self.movie_table_widget.item(row, 0)
            genres_item = self.movie_table_widget.item(row, 1)
            rating_item = self.movie_table_widget.item(row, 2)

            title = title_item.text().lower()
            genres = set(genres_item.text().lower().split('|'))
            rating = float(rating_item.text()) if rating_item.text() else 0.0

            matches_search = search_text in title
            matches_genres = selected_genres.issubset(genres) or self.all_checkbox.isChecked()
            matches_rating = min_rating <= rating <= max_rating if filter_by_rating else True

            if matches_search and matches_genres and matches_rating:
                self.movie_table_widget.setRowHidden(row, False)
            else:
                self.movie_table_widget.setRowHidden(row, True)

    def show_movie_detail(self, item):
        row = item.row()
        title = self.movie_table_widget.item(row, 0).text()
        genres = self.movie_table_widget.item(row, 1).text()
        rating_avg = self.movie_table_widget.item(row, 2).text()
        QMessageBox.information(self, "영화 정보", f"제목: {title}\n장르: {genres}\n평균 평점: {rating_avg}")

    def toggle_all_genres(self):
        if self.all_checkbox.isChecked():
            for checkbox in self.genre_checkboxes:
                checkbox.setEnabled(False)
                checkbox.setChecked(False)
        else:
            for checkbox in self.genre_checkboxes:
                checkbox.setEnabled(True)

    def toggle_rating(self):
        is_checked = self.rating_checkbox.isChecked()
        self.min_rating_box.setEnabled(is_checked)
        self.max_rating_box.setEnabled(is_checked)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
