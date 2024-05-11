import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox
import sqlite3

class MovieListApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Movie List")
        self.initUI()

    def initUI(self):
        # SQLite 데이터베이스 연결
        self.conn = sqlite3.connect('movies.db')
        self.cursor = self.conn.cursor()

        # 장르 선택 콤보 박스 추가
        self.genreComboBox = QComboBox()
        self.genreComboBox.addItem("All Genres")  # 모든 장르를 보여주는 옵션
        self.genreComboBox.addItems(self.get_unique_genres())  # 데이터베이스에서 중복 없이 모든 장르를 가져와서 추가
        self.genreComboBox.currentIndexChanged.connect(self.update_table)  # 콤보 박스 값이 변경될 때마다 테이블을 업데이트

        # 평점 정렬 콤보 박스 추가
        self.ratingComboBox = QComboBox()
        self.ratingComboBox.addItems(["No Sorting", "High to Low", "Low to High"])
        self.ratingComboBox.currentIndexChanged.connect(self.update_table)  # 콤보 박스 값이 변경될 때마다 테이블을 업데이트

        # 데이터베이스에서 가져온 데이터를 테이블 위젯에 표시
        self.tableWidget = QTableWidget()
        self.update_table()  # 초기에는 모든 장르의 영화를 표시

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.genreComboBox)
        layout.addWidget(self.ratingComboBox)
        layout.addWidget(self.tableWidget)
        self.setLayout(layout)

    def get_unique_genres(self):
        # 중복 없이 모든 장르를 가져오는 함수
        self.cursor.execute("SELECT genres FROM movies")
        rows = self.cursor.fetchall()
        all_genres = set()
        for row in rows:
            genres = row[0].split('|')  # 장르를 분할하여 리스트로 변환
            all_genres.update(genres)  # 모든 장르를 추가 (중복 제거됨)
        return sorted(all_genres)

    def update_table(self):
        # 선택한 장르 및 평점 순서에 따라 테이블을 업데이트하는 함수
        selected_genre = self.genreComboBox.currentText()
        selected_rating = self.ratingComboBox.currentText()

        if selected_genre == "All Genres":
            query = "SELECT * FROM movies"
        else:
            query = "SELECT * FROM movies WHERE genres LIKE '%{}%'".format(selected_genre)

        if selected_rating == "High to Low":
            query += " ORDER BY rating_avg DESC"
        elif selected_rating == "Low to High":
            query += " ORDER BY rating_avg ASC"

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        self.tableWidget.clear()  # 테이블 내용을 지우고 새로운 내용을 추가
        # 테이블 위젯의 열 추가
        self.tableWidget.setColumnCount(3)  # 장르를 제외한 열의 개수
        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setHorizontalHeaderLabels(['title', 'genres', 'rating_avg'])

        for i, row in enumerate(rows):
            # 영화의 제목, 장르, 평점 관련 데이터만 표시
            title_item = QTableWidgetItem(row[1])  # title
            genres_item = QTableWidgetItem(row[2])  # genres
            rating_avg_item = QTableWidgetItem(str(row[6]))  # rating_avg

            self.tableWidget.setItem(i, 0, title_item)
            self.tableWidget.setItem(i, 1, genres_item)
            self.tableWidget.setItem(i, 2, rating_avg_item)

    def closeEvent(self, event):
        # 앱이 종료될 때 데이터베이스 연결 종료
        self.conn.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MovieListApp()
    ex.show()
    sys.exit(app.exec_())
