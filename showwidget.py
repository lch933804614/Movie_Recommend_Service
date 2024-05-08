import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
import sqlite3

class MovieListApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Movie List")
        self.initUI()

    def initUI(self):
        # SQLite 데이터베이스 연결
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()

        # 테이블 조회 쿼리 실행
        cursor.execute("SELECT * FROM movies")
        rows = cursor.fetchall()

        # 데이터베이스에서 가져온 데이터를 테이블 위젯에 표시
        tableWidget = QTableWidget()
        tableWidget.setColumnCount(len(rows[0]))
        tableWidget.setRowCount(len(rows))
        tableWidget.setHorizontalHeaderLabels(['movieId', 'title', 'genres', 'imdbId', 'tmdbId', 'rating_count', 'rating_avg'])

        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                tableWidget.setItem(i, j, item)

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(tableWidget)
        self.setLayout(layout)

        # 데이터베이스 연결 종료
        conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MovieListApp()
    ex.show()
    sys.exit(app.exec_())
