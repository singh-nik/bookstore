import os
import csv 

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine=create_engine(os.getenv("database_url"))
db=scoped_session(sessionmaker(bind=engine))

def main():

    f = open("books.csv")
    reader = csv.reader(f)
    for isbn , title , author ,year in reader:
        db.execute("insert into books(isbn,title,author,year) values(:isbn , :title , :author , :year )" ,
        {"isbn":isbn , "title":title , "author":author , "year":year })
        print(f"added book {isbn} title {title} author {author}")
        db.commit()

if __name__=="__main__":
    main()
