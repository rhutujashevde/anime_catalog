# FSND Item Catalog Project


## Introduction

This application provides a list of items within a variety of categories (anime) as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete items.

This RESTful web application is developed using the Python framework Flask along with implementing third-party OAuth authentication ie. Google. Various HTTP methods available are used related to CRUD (create, read, update and delete) operations.

### About this Repo and Database

* app.py - The main python file.
* templates folder - includes all the temlates used in the web application.
    * includes folder - contains the code for the navbar.
* static folder - contains the css and ico file.
* animedb.sqlite - contains three tables
    1. User - id, name
    2. Genre - id, description
    3. Anime - id, description, atype(anime type), genre_id

### PreRequisites

* [Python](https://www.python.org/downloads/)
* [Vagrant](https://www.vagrantup.com/downloads.html)
* [VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
* [Git Terminal](https://git-scm.com/downloads)
* [Flask](http://flask.pocoo.org/docs/1.0/) - pip install flask
* [Flask-Sqlalchemy](http://flask-sqlalchemy.pocoo.org/2.3/) - pip install flask_sqlalchemy


### Configuration file 

* Download and unzip this file: [FSND-Virtual-Machine.zip](https://s3.amazonaws.com/video.udacity-data.com/topher/2018/April/5acfbfa3_fsnd-virtual-machine/fsnd-virtual-machine.zip) This will give you a directory called FSND-Virtual-Machine. It may be located inside your Downloads folder.
* Change to this directory in your terminal with cd. Inside, you will find another directory called vagrant. Change directory to the vagrant directory.


### How to set up and run the app:

* Launch the Git Terminal

* cd to the file/repo containing the code.

1. Launch the Vagrant VM inside Vagrant sub-directory in the downloaded fullstack-nanodegree-vm repository using command:
```
$ vagrant up
```

2. Log in
```
$ vagrant ssh
```

3. Change directory to /vagrant
```
$ vagrant@vagrant:~$ cd /vagrant
```

4. Run this projrct in the virtual machine using
```
$ python app.py
```

* The app runs on [http://localhost:8000/](http://localhost:8000/)

* Press on Login button in order to Log into the website or go to [http://localhost:8000/login](http://localhost:8000/login)

* You can add a new anime or edit/delete the ones already created.

### JSON Endpoints

Genre JSON: /genres.json - Displays all the Genres.

Genre JSON: /genres/<int:genre_id>.json - Displays Animes in that specic Genre.

Anime JSON: /animes/<int:anime_id>.json - Displays a specic Anime json.
