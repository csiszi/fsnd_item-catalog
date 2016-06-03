# Udacity Item Catalog project

## How to run
Make sure you have flask/python installed
run `python database_setup.py` to setup the db,
then `python fakeitems.py` to populate it with a few fake itmes.

To run the project, type `python project.py` and then visit
`http://localhost:5000`

The project is a family todo app, it's only accessible after login.

## CRUD
### Create
You can add new todos by clicking the + icon after the category name
### Read
You can list todos by visiting the main route (/)
### Update
You can toggle a todo by clicking on its name
### Delete
You can delete a todo if you're the owner of it by clicking Delete

## Authentication
You can log in with a google account

## Authorization
Only the owner (usually Mom) can delete a Todo

## JSON
List todos by visiting /todos/JSON