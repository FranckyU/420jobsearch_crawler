import os
import re
import requests
from pony.orm import *
from bs4 import BeautifulSoup

# ===== STORAGE ===============

mysql_host        = os.environ["JOB_CRAWLER_MYSQL_DB_HOST"]
mysql_dn_name     = os.environ["JOB_CRAWLER_MYSQL_DB_NAME"]
mysql_db_user     = os.environ["JOB_CRAWLER_MYSQL_DB_USER"]
mysql_db_password = os.environ["JOB_CRAWLER_MYSQL_DB_PASSWORD"]

db = Database()

class JobAd(db.Entity):
  id                = PrimaryKey(int, auto=True)
  title             = Required(str)
  position_type     = Required(str)
  html_description  = Optional(unicode, sql_type="text", max_len=64000) # caveat of the ORM validation, normally TEXT columns should not have max length
  company_name      = Required(str)
  location          = Required(str)
  salary            = Optional(str)
  page_url          = Required(str)

  _table_options_ = {
    'ENGINE': 'InnoDB'
  }

db.bind(provider='mysql', host=mysql_host, user=mysql_db_user, passwd=mysql_db_password, db=mysql_dn_name, charset='utf8')
db.generate_mapping(create_tables=True)

# ====== CRAWLING ============

def parse_jobs(url):
  page = requests.get(url)
  content = BeautifulSoup(page.content, 'html.parser')

  for page_number in range(1, get_page_count_from(content)+1):
    parse_job_list_by_page(page_number)

def parse_job_list_by_page(page_number):
  page = requests.get(url_for_list_page(page_number))
  content = BeautifulSoup(page.content, 'html.parser')

  for job_url in list(map(lambda element: element["href"], content.select("div.job-list-content a.job-title-420"))):
    extract_job_details(url_for_job_page(job_url))

@db_session
def extract_job_details(url):
  orm_error_count = 0

  try:
    print("Parsing job at %s" % url)

    (_title, _position_type, _description, _company_name, _location, _salary) = [""] * 6

    page = requests.get(url)
    content = BeautifulSoup(page.content, 'html.parser')

    _position_type  = content.select("div.company-info h1 a")[0].get_text().strip()
    _title          = content.select("div.company-info h1 a")[0].previous_sibling.strip()
    _company_name   = content.select("div.company-info h2 a")[0].get_text().strip()

    _location       = content.select("div.company-info h4.job-location a")[0].get_text().strip().replace('\r', '').replace('\n', '')
    _location = " ".join(_location.split())

    for paragraph in content.select("div.container div.padding-right p"):
      if "salary:" in paragraph.get_text().lower():
        pattern = re.compile("salary:", re.IGNORECASE)
        _salary = pattern.sub("", paragraph.get_text()).strip()
      else:
        _description += " ".join(unicode(paragraph).split())

    is_record_in_db = JobAd.select(lambda job: job.page_url == url).count() > 0

    if is_record_in_db:
      JobAd.get(page_url=url).set(title=_title, position_type=_position_type, html_description=_description, company_name=_company_name, location=_location, salary=_salary)
      print("UPDATED")
    else:
      JobAd(title=_title, position_type=_position_type, html_description=_description, company_name=_company_name, location=_location, salary=_salary, page_url=url)
      print("INSERTED")

    commit()
  except pony.orm.core.UnexpectedError:
    if orm_error_count == 0:
      orm_error_count += 1

      if is_record_in_db:
        JobAd.get(page_url=url).set(title=_title, position_type=_position_type, company_name=_company_name, location=_location, salary=_salary)
        print("UPDATED :: without html_description")
      else:
        JobAd(title=_title, position_type=_position_type, company_name=_company_name, location=_location, salary=_salary, page_url=url)
        print("INSERTED :: without html_description")
    else:
      print("ENCODING ERROR on job page -- pass")
  except:
    print("GENERIC ERROR on job page -- pass")

def url_for_list_page(page_number):
  return "https://420jobsearch.com/browse-jobs?page=%s" % page_number

def url_for_job_page(path):
  return "https://420jobsearch.com%s" % path

def get_page_count_from(page_content):
  return int(page_content.select("nav.pagination ul li a")[-1].get_text())

# ======= ENTRY POINT =========

def main():
  parse_jobs(url="https://420jobsearch.com/browse-jobs")

main()