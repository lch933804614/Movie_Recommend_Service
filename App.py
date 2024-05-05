import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.QtGui import QIcon
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData


class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        
        self.setWindowTitle('Movie RC System')
        self.setWindowIcon(QIcon('ClapperBoardIcon.png'))
        self.setGeometry(300, 300, 1000, 1000)
        self.move(300, 300)
        self.resize(1000, 700)

        # 데이터베이스 연결 설정
        db_uri = 'sqlite:///data.db'
        engine = create_engine(db_uri)
        metadata = MetaData()

        # movies 테이블에 연결
        movies = Table('movies', metadata,
                       Column('movieId', Integer, primary_key=True),
                       Column('title', String),
                       Column('genres', String)
                      )
        
        # 데이터베이스와 연결하고 movies 테이블에서 데이터 가져오기
        with engine.connect() as conn:
            query = conn.execute(movies.select())
            movies_list = query.fetchall()
        
        # 영화 리스트를 표시할 QTableWidget 생성
        self.movie_table_widget = QTableWidget()
        self.movie_table_widget.setColumnCount(2)  # 열의 개수 설정
        self.movie_table_widget.setHorizontalHeaderLabels(['Title', 'Genres'])  # 열 제목 설정
        self.movie_table_widget.setColumnWidth(0, 600) # 1열 너비 지정
        self.movie_table_widget.setColumnWidth(1, 400) # 2열 너비 지정
        
        # 영화 리스트를 표에 추가
        for row, movie in enumerate(movies_list):
            title = movie[1]
            genres = movie[2]
            
            self.movie_table_widget.insertRow(row)
            self.movie_table_widget.setItem(row, 0, QTableWidgetItem(title))
            self.movie_table_widget.setItem(row, 1, QTableWidgetItem(genres))
        
        # 수직 레이아웃 생성
        vbox = QVBoxLayout()
        vbox.addWidget(self.movie_table_widget)

        self.setLayout(vbox)
        self.show()


if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = MyApp()
   sys.exit(app.exec_())
