from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, TodoItem, User

engine = create_engine('postgresql://catalog:@localhost:5432/tododb')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Mom", email="mom@udacity.com",
             picture='http://brevard-online.com/wp-content/uploads/2014/05/Just-Another-Mommy_avatar_1399386654.jpg')
session.add(User1)
session.commit()

# Category
category1 = Category(user_id=1, name="Important things")

session.add(category1)
session.commit()

category2 = Category(user_id=1, name="Someday")

session.add(category2)
session.commit()

# Todo items

todo1 = TodoItem(user_id=1, name="Clean up your room", status=True, category_id=1)
session.add(todo1)
session.commit()

todo2 = TodoItem(user_id=1, name="Repair your bike", status=False, category_id=2)
session.add(todo2)
session.commit()



print "added things"