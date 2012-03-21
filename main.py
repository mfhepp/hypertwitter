#!/usr/bin/env python
# -*- coding: utf-8 -*-
# encoding: utf-8
#
# HyperTwitter by Martin Hepp
# Universität der Bundeswehr München
# http://www.heppnetz.de
#

# http://semantictwitter.appspot.com/search.json
# http://semantictwitter.appspot.com/search.atom
# http://semantictwitter.appspot.com/search
# http://semantictwitter.appspot.com/

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from utils import *

import logging

TWEETS = ["""
#iswc09 = #iswc2010 . 
#iswc09 sameas #iswc2010 .
#iswc09 subtag #iswc .
@mfhepp = @martinhepp .
@mfhepp foaf:knows @kidehen .
@mfhepp foaf:name "Martin Hepp .
@mfhepp foaf:birthday "12-31" .

#iswc09 skos:broader #iswc  .

@microsoft a gr:BusinessEntity .
@microsoft rdf:type gr:BusinessEntity .
#munich >translation #muenchen .
@mfhepp >dob "1971-01-01" .
@mfhepp >hasname "Martin Hepp" .
"""
# @mfhepp >attends http://www.iswc2010.org/#conference .
#http://www.iswc2010.org/ >successor http://www.iswc2009.org/ .
]
		
class RDF_XML(webapp.RequestHandler):
	"""
	This handler returns the RDF graph extracted from the given user ID or trust list.
	http://semantictwitter.appspot.com/rdf
	
		u = ID of the Twitter user or list owner
		list (optional) = Twitter ID of the list that contains the hypertagging statements to trust
		p (optional) = password for user u, if list is private
		
	Example:
	http://semantictwitter.appspot.com/rdf?u=hypertw&list=trust
	
	"""
	def get(self):
		user = self.request.get("u")
		pwd = self.request.get("p")
		user_list = self.request.get("list")

		# get all tweets from trust list
		tweets = get_tweets(user=user,pwd=pwd,listID=user_list)
		# tweets = TWEETS
		
		# convert list of tweets to RDF graph
		g =  create_graph(tweets)
		
		self.response.headers['Content-Type'] = "application/rdf+xml"
		self.response.out.write(g.serialize(format="rdf/xml"))


class SearchHTML(webapp.RequestHandler):
	"""
	This handler expands the twitter search API for HTML output. 
	
	http://semantictwitter.appspot.com/search
	
	It supports all twitter parameters plus:
		u = ID of the Twitter user or list owner
		list (optional) = Twitter ID of the list that contains the hypertagging statements to trust
		p (optional) = password for user u, if list is private
	
	Example:
	http://semantictwitter.appspot.com/search?q=%23munich?u=hypertw&list=trust	
		
	"""
	def get(self):
		format = ""
		uri = process_query(self,format=format)
		self.redirect(uri)

class SearchAtom(webapp.RequestHandler):
	"""
	This handler expands the twitter search API for Atom output. 
	
	http://semantictwitter.appspot.com/search.atom
	
	It supports all twitter parameters plus:
		u = ID of the Twitter user or list owner
		list (optional) = Twitter ID of the list that contains the hypertagging statements to trust
		p (optional) = password for user u, if list is private

	Example:
	http://semantictwitter.appspot.com/search.atom?q=%23munich?u=hypertw&list=trust
				
	"""

	def get(self):
		format = ".atom"
		uri = process_query(self,format=format)
		self.redirect(uri)

class SearchJSON(webapp.RequestHandler):
	"""
	This handler expands the twitter search API for JSON output. 
	
	http://semantictwitter.appspot.com/search.json
	
	It supports all twitter parameters plus:
		u = ID of the Twitter user or list owner
		list (optional) = Twitter ID of the list that contains the hypertagging statements to trust 
		p (optional) = password for user u, if list is private

	Example:
	http://semantictwitter.appspot.com/search.json?q=%23munich?u=hypertw&list=trust
			
	"""

	def get(self):
		format = ".json"
		uri = process_query(self,format=format)
		self.redirect(uri)	
	
def main():
	application = webapp.WSGIApplication([('/search', SearchHTML),('/search.atom', SearchAtom),('/search.json', SearchJSON),('/rdf', RDF_XML)],debug=True)
	util.run_wsgi_app(application)
	
if __name__ == '__main__':
	main()

