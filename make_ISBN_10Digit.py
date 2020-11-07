import os,csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine=create_engine(os.getenv("database_url"))
db=scoped_session(sessionmaker(bind=engine))

def main():
   t=0
   reader = db.execute("select * from books").fetchall()
   for isbn , title , author ,year in reader:
        if len(isbn)<10:
           t=t+1
           s=isbn
           while(len(s)<10):
               s="0" +s
           db.execute("update books set isbn=(:s) where isbn=(:isbn)",{"s":s , "isbn":isbn})
           
           print(f"isbn changed to {isbn}")
           db.commit()
           print(t)

if __name__=="__main__":
    main()