# WELCOME

This project is a Python written web crawler that scraps for job ads at https://420jobsearch.com/ and stores them inside a MySQL database.

## DEPENDENCIES

- Requests [http://docs.python-requests.org/en/master/]
- Pony ORM [https://ponyorm.com/]
- BeautifulSoup [https://www.crummy.com/software/BeautifulSoup/]

I'm using Anaconda [https://conda.io] to manage an isolated python environment containing these dependencies. Please check [https://conda.io/docs/user-guide/getting-started.html] for instructions
An `environment.yml` file is already shipped which contains all things necessary to setup an isolated conda environment for you.

If you prefer doing things differently, just make sure these libs are installed either through pip or any other tools.

## SETUP

1- Setup the conda environment
`conda env create -f environment.yml` (done from `conda env export > environment.yml`)

2- Activate the environment
Windows: `activate myenv`
macOS and Linux: `source activate myenv`

3- Have MySQL installed and the following environment variables defined to access the Database:
  JOB_CRAWLER_MYSQL_DB_HOST
  JOB_CRAWLER_MYSQL_DB_NAME
  JOB_CRAWLER_MYSQL_DB_USER
  JOB_CRAWLER_MYSQL_DB_PASSWORD

4- Run it
`python main.py`

## HOW IT WORKS

Actually it fetches the pages sequentially:

1- goes to homepage
2- determines the total pages length from the pagination at the bottom of the page
3- generates a url for each page in the pagination and visits each one
4- on each list page, follows the link of each job ad
5- parse the job page and inserts/update database records

## CAN IT BE IMPROVED ?

Of course YES :) , the most natural way to scrap on the web is doing it concurrently.
I'm actually using python 2.7 so I could only use multithreading or multiprocessing [or greenlets] to speed up things. 
But here we're IO bound thus the best way to process these jobs concurrently is using python 3 asyncio, WIP.

## KNOWN ISSUES

- We can quickly reach the request cap limit. Need request spacing a strategy to overcome that, with an external supervisor like a crontab to fetch the pages in small batches.
- Encoding issue between  Python-ORM-MySQL, I bypassed it by not storing the job description