from embedly import Embedly
from api_keys import embedly_key
from classes import Link
from google.appengine.ext import db
import datetime
import re
import feedparser
from bs4 import BeautifulSoup
import uuid
from classes import Email


configuration = {"vote_deflator":2}


def embedly_link(URL):
	#Takes a URL, returns a populated Link object
	#Returns "error" if Embedly API fails
	client = Embedly(embedly_key)
	response = client.extract(URL)
	try:
		#Get link information from Embedly
		headline = response['title']
		URL = clean_url(response['url'])
		summary = response['description']
		source = response['provider_name']
		path = page_path(headline)
		keywords_response = response['keywords']
		keyword1 = str(keywords_response[0]['name'])
		keyword2 = str(keywords_response[1]['name'])
		keyword3 = str(keywords_response[2]['name'])
		keyword4 = str(keywords_response[3]['name'])
		keyword5 = str(keywords_response[4]['name'])

		#Create Link object with info from Embedly
		link = Link(headline = headline, url = URL, source = source, summary = summary, 
			path = path, keyword1 = keyword1, keyword2 = keyword2, keyword3 = keyword3, 
			keyword4 = keyword4, keyword5 = keyword5, votes = 0)
		return link
	except:
		return "error"

def clean_url(url):
    if "?" in url:
        return url.split("?")[0]
    else:
        return url

def is_link_in_database(URL):
	#Returns Link object if URL already in Link database, else returns False
	qry = db.Query(Link).filter("url =", URL)
	result = qry.get()
	if result:
		return result
	else:
		return False

def is_email_in_database(email):
	#Returns Email object if email already in database, else returns False
	qry = db.Query(Email).filter("email =", email)
	result = qry.get()
	if result:
		return result
	else:
		return False

def hotness(link):
	#Calculate hotness score for a Link, update hotness attribute, return Link
	#Doesn't put the Link to the database; that needs to be done with returned object
	#Hotness = (# of days between creation of link and origin date 1/23/16)
	# + (number of votes, divided by vote_deflator variable in configuration)
    origin = datetime.datetime(2016, 1, 23)
    diff = link.created - origin
    days = float(diff.days) + (float(diff.seconds)/float(86400))
    link.hotness = float(days) + (float(link.votes)/configuration['vote_deflator'])
    return link

def upvote(URL):
	#Takes URL, increments votes on Link object by one, updates hotness, updates database
    qry = db.Query(Link).filter("url =", URL)
    link = qry.get()
    link.votes = link.votes + 1
    hotness(link)
    link.put()


def session_voting(handler, URL):
	#When a user clicks upvote, checks if a user has upvoted a particular link this session
	#Returns True or False; if False, changes vote status
	has_voted = handler.session.get(URL)
	if not has_voted:
		handler.session[URL] = True
		upvote(URL)

def page_path(headline):
    #Returns today's date, hyphenated, followed by lowercase headline, hypthenated
    return str(datetime.date.today()) + "-" + "-".join(re.findall("[a-zA-Z]+", headline)).lower()


def rss_parse(source):
	#Take a source object with an RSS feed and enter new links into db
	feed = feedparser.parse(source.rss)
	#If source has exclude words, break exclude_words string field into 
	#list of words that exclude a link if in headline
	if source.exclude_words:
		exclude_words = source.exclude_words.split(":")
	else:
		exclude_words = ""

	#Check what the last link from this source last time was
	last_link = source.last_link
	source.last_link = feed.entries[0][source.link_tag]

	for a in feed.entries:
		if a[source.link_tag] == last_link:
			break
		else:
			#If there are no exclude_words in the headline
			if not any(word in a['title'].lower() for word in exclude_words):
				#Hit the Embedly API
				response = embedly_link(a[source.link_tag])
				if response != "error":
					database_response = is_link_in_database(response.url)
					if database_response == False:
						#Calculate a hotness score for the new link
						response = hotness(response)
						#Set submitted_by attribute to name of the rss feed
						response.submitted_by = source.name
						#add to database
						response.put()
					else:
						#If link is already in the database, get that link
						if source.name not in database_response.submitted_by:
							#add a vote
							database_response.votes = database_response.votes + 1
							#recalculate hotness
							database_response = hotness(database_response)
							#add source name to the submitted_by source list
							database_response.submitted_by = database_response.submitted_by + ":" + source.name
							#update database
							database_response.put()
	source.put()

### Pseudo code to cut down on RSS db calls
### Each source has a "last seen link" attribute -- the most recent link from the last time you hit it
### for each rss source: while entry not equal to source.last_seen_link: parse. stop the loop when you hit the last_seen_link



def blog_rec_parser(source):
	#Takes an RSS feed, returns list of URLs to posts mentioned in link roundup posts
    feed = feedparser.parse(source.rss)
    url_list = []
    for entry in feed.entries:
        headline = entry['title']
        if source.include_words in headline:
        	#If the post's headline mentions terms indicating it's a link roundup post
            post = entry.content[0]['value']
            soup = BeautifulSoup(post)
            #if soup.body is not None:
            for link in soup.find_all('a'):
                	url = link.get('href')
                	if url != source.exclude_words and source.include_words.replace(' ', '-').lower() not in url:
                		#If exclude words aren't present and if it isn't just a link to the site's homepage add to list
                		url_list.append(url)
    return url_list

def aggregator_parse(list_of_urls, source_name):
	#Takes list of URLs, name of the aggregator as a string. Enters in db if appropriate
	for a in list_of_urls:
		response = embedly_link(a)
		if response != "error":
			#If the link is NOT already in the Link database, put it there
			qry = is_link_in_database(response.url)
			if qry == False:
				#If link not in database, calculate hotness, add to db
				response = hotness(response)
				response.submitted_by = source_name
				response.put()
			elif source_name not in qry.submitted_by:
				#If link is in database but it wasn't submitted by thoma feed
				qry.votes = qry.votes + 1
				qry = hotness(qry)
				#add thoma source name to the submitted_by source list
				qry.submitted_by = qry.submitted_by + ":" + source_name
				qry.put()

def is_email_address(email):
	#Checks if string looks like an email
	email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
	if email_regex.match(email):
		return True
	else:
		return False

def create_email_key():
	unique = False
	while unique == False:
		email_key = str(uuid.uuid4())
		qry = db.Query(Email).filter("email_key =", email_key)
		if not qry.get():
			unique = True
	
	return email_key