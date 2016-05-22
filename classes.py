from google.appengine.ext import db


class Link(db.Model):
	#Links are the basic unit of content
	headline = db.StringProperty(required = True)
	url = db.StringProperty(required = True)
	summary = db.TextProperty(required = True)
	#Source examples: "TheAtlantic.com"
	source = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add = True)
	#Submitted_by examples: user, RSS, Twitter
	submitted_by = db.StringProperty()
	#Page path for the site
	path = db.StringProperty(required = True)
	
	keyword1 = db.StringProperty()
	keyword2 = db.StringProperty()
	keyword3 = db.StringProperty()
	keyword4 = db.StringProperty()
	keyword5 = db.StringProperty()
	
	votes = db.IntegerProperty()
	#Hotness is a function of votes and time
	hotness = db.FloatProperty()

class Source(db.Model):
	#A source periodically sends Links to the app -- examples include RSS feeds
	name = db.StringProperty(required = True)
	rss = db.StringProperty()
	exclude_words = db.StringProperty()
	include_words = db.StringProperty()
	#format: source:source:source all lower
	source_type = db.StringProperty()
	#link tag indicates where in the RSS feed the link is
	#default should be "link"
	link_tag = db.StringProperty()
	#Keep a record of the last link from this feed to minimize db queries
	last_link = db.StringProperty()


class Email(db.Model):
	#Handles emails and unsubscrube status
	email = db.StringProperty(required = True)
	#Active == True if currently subscribed
	active = db.BooleanProperty(required = True)
	#Key is for confirmation and unsubscribe URLs
	email_key = db.StringProperty()
	#Signup confirmations expire, hence signup_time
	signup_time = db.DateTimeProperty(auto_now_add = True)
