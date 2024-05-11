import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QLineEdit, QMessageBox, QPushButton, QCheckBox, QHBoxLayout, QLabel, QDoubleSpinBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Movie RC System')
        self.setWindowIcon(QIcon('ClapperBoardIcon.png'))
        self.setGeometry(450, 150, 1000, 800)

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

        self.setLayout(vbox)
        self.show()

    # 영화 제목 클릭 시 상세정보 표시
    def show_movie_detail(self, item):
        row = item.row()
        title = self.movie_table_widget.item(row, 0).text()
        genres = self.movie_table_widget.item(row, 1).text()

        message = f"Title: {title}\nGenres: {genres}"
        QMessageBox.information(self, "MovieInfo", message)

    def toggle_rating(self, state):
        # 평점 검색 체크박스가 선택된 경우 평점 검색을 활성화합니다.
        self.min_rating_box.setEnabled(state == Qt.Checked)
        self.max_rating_box.setEnabled(state == Qt.Checked)

    def toggle_all_genres(self, state):
        # "전체" 체크박스가 선택된 경우 장르 체크박스를 비활성화합니다.
        for checkbox in self.genre_checkboxes:
            checkbox.setEnabled(state != Qt.Checked)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
