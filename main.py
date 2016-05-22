#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from webapp2_extras import sessions
from google.appengine.ext import db
from google.appengine.api import mail
import jinja2
import os
from classes import Link
from classes import Source
from classes import Email
from utilities import embedly_link
from utilities import is_link_in_database
from utilities import hotness
from utilities import upvote
from utilities import session_voting
from utilities import rss_parse
from utilities import blog_rec_parser
from utilities import aggregator_parse
from utilities import is_email_address
from utilities import is_email_in_database
from utilities import create_email_key
from api_keys import embedly_key
from utilities import configuration
from random import shuffle
import datetime
from datetime import timedelta



#Set template directory
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
#Set up jinja environment
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)



class BaseHandler(webapp2.RequestHandler):
	#Base handler captures session data which is used to manage voting
	def dispatch(self):
		# Get a session store for this request.
		self.session_store = sessions.get_store(request=self.request)

		try:
			# Dispatch the request.
			webapp2.RequestHandler.dispatch(self)
		finally:
			# Save all sessions.
			self.session_store.save_sessions(self.response)

	@webapp2.cached_property
	def session(self):
		# Returns a session using the default cookie key.
		return self.session_store.get_session()



class MainHandler(BaseHandler):
	#Front page
	def get(self):
		links = db.Query(Link).order('-hotness')
		links = links.run(limit=10)
		links = list(links)
		template_variables = {'links' : links, 'nextpage' : 2, 'pageroot' : 'page'}
		permalink_template = jinja_env.get_template('homepage.html')
		self.response.write(permalink_template.render(template_variables))
	
	def post(self):
		vote = self.request.get('Upvote')
		#Increment votes on upvoted link by +1 if user hasn't already voted on Link
		session_voting(self, vote)
		self.redirect("/")

class Past(BaseHandler):
	#Archive pages ranked by hotness
	def get(self, path):
		try:
			path = int(path)
			links = db.Query(Link).order('-hotness')
			links = links.run(limit=10, offset = path * 10)
			links = list(links)
			template_variables = {'links' : links, 'nextpage' : path+1, 'pageroot' : 'page'}
			permalink_template = jinja_env.get_template('homepage.html')
			self.response.write(permalink_template.render(template_variables))
		except:
			self.redirect("/")
	
	def post(self, path):
		vote = self.request.get('Upvote')
		#Increment votes on upvoted link by +1 if user hasn't already voted on Link
		session_voting(self, vote)
		self.redirect(path)

class Newest(BaseHandler):
	#Newest links page
	def get(self):
		links = db.Query(Link).order('-created')
		links = links.run(limit=10)
		links = list(links)
		template_variables = {'links' : links, 'nextpage' : 2, 'pageroot' : 'newest'}
		permalink_template = jinja_env.get_template('newest.html')
		self.response.write(permalink_template.render(template_variables))
	
	def post(self):
		vote = self.request.get('Upvote')
		#Increment votes on upvoted link by +1 if user hasn't already voted on Link
		session_voting(self, vote)
		self.redirect("/newest")

class Daily(BaseHandler):
	#The top links from the past 24 hours
	def get(self):
		#Get all links posted within past 24 hours
		yesterday = datetime.datetime.now() + timedelta(days=-1)
		links = db.Query(Link).filter("created >=", yesterday)
		links = links.run()
		links = list(links)
		#Sort by number of votes
		links.sort(key = lambda Link: -Link.votes)
		links = links[0:30]
		template_variables = {'links' : links, 'nextpage' : 2, 'pageroot' : 'newest'}
		permalink_template = jinja_env.get_template('newest.html')
		self.response.write(permalink_template.render(template_variables))

	def post(self):
		vote = self.request.get('Upvote')
		#Increment votes on upvoted link by +1 if user hasn't already voted on Link
		session_voting(self, vote)
		self.redirect("/daily")

class NewPast(BaseHandler):
	#Archive pages ranked by recency
	def get(self, path):
		try:
			path = int(path)
			links = db.Query(Link).order('-created')
			links = links.run(limit=10, offset = path * 10)
			links = list(links)
			template_variables = {'links' : links, 'nextpage' : path+1, 'pageroot' : 'newest'}
			permalink_template = jinja_env.get_template('newest.html')
			self.response.write(permalink_template.render(template_variables))
		except:
			self.redirect("/")
	
	def post(self, path):
		vote = self.request.get('Upvote')
		#Increment votes on upvoted link by +1 if user hasn't already voted on Link
		session_voting(self, vote)
		self.redirect(path)

class UniqueLink(BaseHandler):
	#Pages for each Faction Link object
	def get(self, path):
		link = db.Query(Link).filter("path =", path)
		template_variables = {'link' : link.get()}
		permalink_template = jinja_env.get_template('permalink.html')
		self.response.write(permalink_template.render(template_variables))
	def post(self, path):
		vote = self.request.get('Upvote')
		#Increment votes on upvoted link by +1 if user hasn't already voted on Link
		session_voting(self, vote)
		self.redirect(path)

class TagHandler(BaseHandler):
	#Page for each keyword attribute
	def get(self, path):
		term = path

		#Query all 5 keyword fields for the tag
		qry1 = db.Query(Link).filter("keyword1 =", term).order('-hotness')
		qry2 = db.Query(Link).filter("keyword2 =", term).order('-hotness')
		qry3 = db.Query(Link).filter("keyword3 =", term).order('-hotness')
		qry4 = db.Query(Link).filter("keyword4 =", term).order('-hotness')
		qry5 = db.Query(Link).filter("keyword5 =", term).order('-hotness')

		#Run queries and turn into lists
		links1 = list(qry1.run(limit=100))
		links2 = list(qry2.run(limit=100))
		links3 = list(qry3.run(limit=100))
		links4 = list(qry4.run(limit=100))
		links5 = list(qry5.run(limit=100))

		links = list(links1 + links2 + links3 + links4 + links5)

		template_variables = {'tag' : term, 'links' : links}
		permalink_template = jinja_env.get_template('tags.html')
		self.response.write(permalink_template.render(template_variables))

class NewLinkHandler(BaseHandler):
	#Page to handle new links
    def get(self):
        newlink_template = jinja_env.get_template('submitlink.html')
        self.response.write(newlink_template.render())

    def post(self):
		#If anti-spam field is filled in incorrectly, redirect to homepage
		spam = self.request.get('spam')
		if spam != '4':
			self.redirect("/")
		else:
			#If not spam, get link details from Embedly
			submitted_url = self.request.get('URL')
			response = embedly_link(submitted_url)
			if response == "error":
				self.redirect("/")
			else:
				#If the link is NOT already in the Link database, put it there
				qry = is_link_in_database(response.url)
				if qry == False:
					response = hotness(response)
					#Set submitted_by attribute to "user" since a user submitted the link
					response.submitted_by = "user"
					response.put()
					self.redirect("/")
				else:
					qry.votes = qry.votes + 1
					qry = hotness(qry)
					qry.put()
					self.redirect("/")

class About(webapp2.RequestHandler):
	def get(self):
		about_template = jinja_env.get_template('about.html')
		self.response.write(about_template.render())

class RSS_cron(webapp2.RequestHandler):
	def get(self):
		qry = db.Query(Source).filter("source_type =", "RSS")
		for a in qry:
			rss_parse(a)
			self.response.write("it worked")

class Daily_cron(webapp2.RequestHandler):
	def get(self):
		from sources import global_aggregators
		aggregators = global_aggregators
		shuffle(aggregators)
		for a in aggregators:
			links = blog_rec_parser(a)
			aggregator_parse(links, a.name)

		self.response.write("it worked")

class Email_cron(webapp2.RequestHandler):
	#Sending daily emails
	def get(self):

		#Get all links posted within past 24 hours
		yesterday = datetime.datetime.now() + timedelta(days=-1)
		links = db.Query(Link).filter("created >=", yesterday)
		links = links.run()
		links = list(links)
		#Sort by number of votes
		links.sort(key = lambda Link: -Link.votes)
		links = links[0:5]

		qry = db.Query(Email).filter("active", True)
		active_emails = list(qry)

		for a in active_emails:

			template_variables = {'links' : links, 'emailkey' : a.email_key}
			permalink_template = jinja_env.get_template('plain_jane_email.html')
			email_body = permalink_template.render(template_variables)

			try:
				mail.send_mail(sender = "Faction <faction@factionapp-1227.appspotmail.com>",
				to = a.email,
				subject = 'Faction Daily',
				body = "plain text version not available",
				html = email_body)
				self.response.write("worked")
			except:
				self.response.write("fail")


class sandbox(webapp2.RequestHandler):
	#Sandbox just for testing
	def get(self):
		self.response.write("This is a testing page.")

class Newsletter(BaseHandler):
	#Handles newsletter signup
	def get(self):
		newlink_template = jinja_env.get_template('emailsignup.html')
		self.response.write(newlink_template.render())

	def post(self):
		#If anti-spam field is filled in incorrectly, redirect to homepage
		spam = self.request.get('spam')
		if spam != '4':
			self.redirect("/")
		else:
			#If not spam, check if email is correct
			email = self.request.get('email')
			if is_email_address(email) == True:
				#Check if email is already in database
				qry = is_email_in_database(email)
				#If not, add it
				if qry == False:
					email_key = create_email_key()
					new_email = Email(email = email, active = False, email_key = email_key)
					new_email.put()

					#Send confirmation email
					template_variables = {'emailkey' : email_key}
					permalink_template = jinja_env.get_template('confirmation_email.html')
					email_body = permalink_template.render(template_variables)
					try:
						mail.send_mail(sender = "Faction <faction@factionapp-1227.appspotmail.com>",
							to = email,
							subject = 'Faction Email Confirmation',
							body = "Plain text version not available.",
							html = email_body)
						template_variables = {'message' : "You should receive a confirmation email shortly."}
						message_template = jinja_env.get_template('message.html')
						self.response.write(message_template.render(template_variables))
						#self.response.write("You should receive a confirmation email")
					except:
						template_variables = {'message' : "Sorry, something went wrong. Please try again."}
						message_template = jinja_env.get_template('message.html')
						self.response.write(message_template.render(template_variables))
				elif qry.active == False:
					#If email in database but not active subscriber (from previous unsubscribe)
					
					#Set confirmation email time to now
					qry.signup_time = datetime.datetime.now()
					qry.put()
					
					#Send confirmation email
					template_variables = {'emailkey' : qry.email_key}
					permalink_template = jinja_env.get_template('confirmation_email.html')
					email_body = permalink_template.render(template_variables)
					try:
						mail.send_mail(sender = "Faction <faction@factionapp-1227.appspotmail.com>",
							to = email,
							subject = 'Faction Email Confirmation',
							body = "Plain text version not available.",
							html = email_body)
						template_variables = {'message' : "You should receive a confirmation email shortly."}
						message_template = jinja_env.get_template('message.html')
						self.response.write(message_template.render(template_variables))
						
					except:
						template_variables = {'message' : "Sorry, something went wrong. Please try again."}
						message_template = jinja_env.get_template('message.html')
						self.response.write(message_template.render(template_variables))
				
				elif qry.active == True:
					template_variables = {'message' : "You're already signed up for the Faction newsletter."}
					message_template = jinja_env.get_template('message.html')
					self.response.write(message_template.render(template_variables))

				else:
					template_variables = {'message' : "Sorry, there's been an error. Please try again."}
					message_template = jinja_env.get_template('message.html')
					self.response.write(message_template.render(template_variables))


			else:
				template_variables = {'message' : "That doesn't look like a valid email address. Please try again."}
				message_template = jinja_env.get_template('message.html')
				self.response.write(message_template.render(template_variables))

class Confirmation(BaseHandler):
	#Open email confirmation links sent in confirmation emails, set Active to true
	def get(self, path):
		email_key = path
		qry = db.Query(Email).filter("email_key =", email_key)
		result = qry.get()
		#Check if confirmation email was within the last day
		diff = datetime.datetime.now() - result.signup_time
		if result and diff.days < 1: 
			result.active = True
			result.put()
			self.response.write("You're active")
		else:
			self.response.write("Error")

class Unsubscribe(BaseHandler):
	#Unsubscribe those who click unsubscribe link in newsletter, set Active to False
	def get(self, path):
		email_key = path
		qry = db.Query(Email).filter("email_key =", email_key)
		if qry.get():
			result = qry.get()
			result.active = False
			result.put()
			self.response.write("You're unsubscribed.")
		else:
			self.response.write("Error")


config = {}
config['webapp2_extras.sessions'] = {
	'secret_key': 'some-secret-key',
}

app = webapp2.WSGIApplication([
    ('/?', MainHandler), ('/submitlink/?', NewLinkHandler),('/newest/?', Newest), ('/about/?',About),
    ('/page/([0-9a-zA-Z_\-]+)', Past), ('/sandbox', sandbox), ('/newest/([0-9a-zA-Z_\-]+)', NewPast),
    ('/rss_cron/?', RSS_cron), ('/daily_cron/?', Daily_cron), ('/email_cron/?', Email_cron),
    ('/tag/([0-9a-zA-Z_\-]+)', TagHandler), ('/newsletter/?', Newsletter), ('/daily/?', Daily),
    ('/confirmation/([0-9a-zA-Z_\-]+)', Confirmation), ('/unsubscribe/([0-9a-zA-Z_\-]+)', Unsubscribe),
    ('/([0-9a-zA-Z_\-]+)', UniqueLink)
], debug=True, config=config)
