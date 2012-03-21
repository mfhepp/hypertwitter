#!/usr/bin/env python
# -*- coding: utf-8 -*-
# encoding: utf-8
#
# TODO
# http://github.com/simplegeo/python-oauth2
# maybe support URIs in <> as direct ones.
# ederef via SPARQL describe - http://uriburner.com/sparql?default-graph-uri%3D%26should-sponge%3D%26query%3DDESCRIBE%20%2A%20WHERE%20%7B%3Chttp%3A%2F%2Fsemantictwitter.appspot.com%2Fid%2Ftags%2Flinux%3E%20%3Fp%20%3Fo%7D%26format%3Dapplication%2Frdf%2Bxml%26debug%3Don%26timeout%3D
# check why http://semantictwitter.appspot.com/rdf?u=gycheng does not work
# check why http://semantictwitter.appspot.com/rdf?u=juum return 400 error
# issue warning to user if user parameter is missing
# fix id/data/http://www.microsoft.com issue (quote!)
# @mfhepp no entailed triples for #tag creators re. #hypertwitter? There should be a link between my identifier and each tag I create.
# @hypertw How far do you go in user's history of tweets to retrieve triples? 
# How to discover friends' trusted (semantic) list?
# @hubject the #hypertwitter query expansion part will soon include transitivtity (but only for 1 & 2 hops in order to not break twitter :-) )
# @mfhepp http://bit.ly/a7DxeT ok. I also want to navigate via: http://bit.ly/dxfOvu which needs doc->entity relation #linkeddata #nanotation
# add more prefixes: ctag etc.
# Store public URIs in DB Task List  
# Store RDF for public users in DB (BLOB)
# Archive Handler that returns a ZIP containing all RDFs
# New Handler that returns html+rdfa list of public URIs
# Dereference data, user, tags, property IDs via skeleton in rdf/xml and html+rdfa, and maybe n3
# Cron job: 
# - send all unprocessed URIs to URI burner, PTSW
# - update all existing URIs
# symmetry of sameas, equivalentTag
# transitivity of broader (maybe just 1 hop)
# serve n3, html,...
# polish and add LPGL stuff & publish
# Options:
# fetch more than 200 tweets from trust list
# memcache graph for users ?
# oauth for app, http://github.com/tav/tweetapp/blob/master/standalone/twitter_oauth_handler.py
"""
Alexandre's input
I'm wondering if:

- you can link to semantictweet to give FOAF URIs to each user (and not only a sioc:User)

- you could add the ability to MOAT-ify the tags, using, e.g.

#apple = http://dbpedia.org/resource/Apple_Inc.

That may lead to

tags:apple moat:Meaning [
	moat:meaningURI <http://dbpedia.org/resource/Apple_Inc.> .
	foaf:maker <http://semantictweet.com/user#id>
] .

- if there's a way to query the data, ideally in real-time (see [1] that I'll tweet in a few minutes)

"""

"""
utils.py

Module for processing details of http://semantictwitter.appspot.com

Created by Martin Hepp on 2010-02-11.
Copyright (c) 2010 Universität der Bundeswehr. All rights reserved.
"""

USRID = "<insert a valid twitter user ID>" 
USRPW = "<insert twitter password>" 

import urllib, urllib2
import logging
import rdflib
import re

PARAMETERS = ['callback', 'lang', 'locale', 'rpp', 'page', 'since_id', 'geocode', 'show_user']
SEARCH_URI = "http://search.twitter.com/search"
# http://api.twitter.com/1/user/lists/list_id/statuses.format
# example http://api.twitter.com/1/cygri/lists/semweb/statuses.xml
# or http://api.twitter.com/1/hypertw/lists/trust/statuses.xml
LIST_URI = "http://api.twitter.com/1/%s/lists/%s/statuses.xml"   

# USER_URI = "http://twitter.com/statuses/user_timeline/%s.xml"
# example: http://api.twitter.com/1/statuses/user_timeline/hypertw.xml
# http://api.twitter.com/1/statuses/user_timeline.format

USER_URI = "http://api.twitter.com/1/statuses/user_timeline/%s.xml"

USER_AGENT = "HeppTwit 1.0"

T_DATA = rdflib.Namespace("http://semantictwitter.appspot.com/id/data/")
T_TAGS = rdflib.Namespace("http://semantictwitter.appspot.com/id/tags/")
T_PROPS = rdflib.Namespace("http://semantictwitter.appspot.com/id/properties/")
T_USERS = rdflib.Namespace("http://semantictwitter.appspot.com/id/users/")

FOAF = rdflib.Namespace("http://xmlns.com/foaf/0.1/")
TAG = rdflib.Namespace("http://www.holygoat.co.uk/owl/redwood/tag/")
GR = rdflib.Namespace("http://purl.org/goodrelations/v1#")
SIOC = rdflib.Namespace("http://rdfs.org/sioc/ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
DC = rdflib.Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = rdflib.Namespace("http://purl.org/dc/terms/")
REV = rdflib.Namespace("http://purl.org/stuff/rev#")

#list of supported prefixes and their namespace objects
curies = [('foaf',FOAF), ('tag', TAG), ('gr', GR), ('sioc', SIOC), ('rdfs', RDFS), ('rdf', RDF), \
('skos', SKOS),	('owl', OWL), ('dc', DC), ('dcterms', DCTERMS), ('rev', REV)]


def process_query(connection,format):
	"""
	process_query(connection,format)
		This method expands and relays the original request and returns the the URI with expanded query as a parameter for a http redirect
		format: {""|".atom"|".json"}

	"""
	user = connection.request.get("u")
	pwd = connection.request.get("p")
	user_list = connection.request.get("list")
	
	# get all tweets from the trusted list
	tweets = get_tweets(user=user,pwd=pwd,listID=user_list)
		
	# derive RDF graph from the hidded semantics in the trusted posts
	g =  create_graph(tweets)
	
	# get original query
	q = connection.request.get("q")
	# unencode
	q = urllib.unquote(q)
	# expand query based on statements in trust list	
	q2 = expand_query(query=q,graph=g)
	
	# carry along all other parameters 
	values = fetch_twitter_parms(connection)
	 
	# replace query string by expanded query
	values['q'] = q2
	data = urllib.urlencode(values)

	# compile new URI
	uri = SEARCH_URI+format+"?"+data
		
	# The format is simply used to change the twitter REST URI:
	# http://search.twitter.com/search.json
	# http://search.twitter.com/search.atom
	# http://search.twitter.com/search
	
	return uri
	
def fetch_twitter_parms(connection):
	"""
	fetch_twitter_parms(connection)
		Fetches all parameters that the twitter REST API supports natively, 
		so that they can be carried over to the expanded query.
		
	"""
	p = {}
	for parameter in PARAMETERS:
		value = connection.request.get(parameter)
		if value != "":
			p[parameter] = value
	return p
	
def get_tweets(user="",pwd="",listID=""):
	"""
	get_tweets(user="",pwd="",list=""):
		gets the last 200 tweets from the given user or trust list.
		This is the raw data for harvesting the semantic relationships between hashtags and user IDs and the RDF graph in general.
		If the list or user status is protected, the password of the list owner or user must be provided.
		
	"""	
	if listID != "":
		uri = LIST_URI % (user,listID)
		logging.info("LISTID found, uri = %s" % uri)
	else:
		uri = USER_URI % user
		logging.info("LISTID not found, uri = %s" % uri)
	
	logging.info(" URI:%s" % uri)
	
	user_agent = USER_AGENT
	headers = {'User-Agent' : user_agent }

	# add authentication hash, if user and password are provided
	if user != "" and pwd !="":
		import base64
		base64string = base64.encodestring('%s:%s' % (user, pwd))[:-1]
		headers['Authorization'] ="Basic %s" % base64string
		
	# use hypertw account if no pwd provided to avoid blacklisting
	else:
		import base64
		base64string = base64.encodestring('%s:%s' % (USRID, USRPW))[:-1]
		headers['Authorization'] ="Basic %s" % base64string
		
	# TODO: maybe fetch more than 200 tweets from trust list; simple loop (API limit is 200 per page)
	
	# Twitter uses different parameter names for the status vs. list API
	if listID != "":
		values = {'per_page':'200'} 
	else:
		values = {'count':'200'}
	
	data = urllib.urlencode(values)	
	logging.info(" RDF-XML: uri=%s,data=%s,headers=%s" % (uri,data,headers))
	final_url=uri+"?"+data
	logging.info("FINAL URL: %s" % final_url)
	req = urllib2.Request(url=uri+"?"+data+"&",headers=headers)
	response = urllib2.urlopen(req)
	
	# get all tweets from the trust list as XML
	content = response.read()
		
	# parse xml and fetch tweets <text>tweet</text>
	tweets = []
	from xml.dom.minidom import parseString
	dom = parseString(content)
	tweetnodes = dom.getElementsByTagName("text")
	for tweet in tweetnodes:
		text = getText(tweet.childNodes)
		tweets.append(text)
		
	return tweets		
	
def create_graph(tweets):
	"""
	create_graph(tweets)
		parses the given list of tweets for semantic statements (hypertwitter statements) and returns it as a rdflib.ConjunctiveGraph
	"""
	g = rdflib.ConjunctiveGraph()
	
	# regular expression that finds s,p,o triples in text / tweets
	
	# ARGG! ugly &gt; instead of > bug took me a long time to find!

	expression = r'((#|@)[-_a-zA-Z0-9\.]+|http://[-_a-zA-Z0-9\./?&%#]+)' + \
r'\s*' + \
r'(=|sameas|subtag|(&gt;|foaf:|tag:|gr:|sioc:|rdfs:|rdf:|skos:|owl:|dc:|dcterms:|rev:)[-_a-zA-Z0-9]+)'+ \
r'\s*' + \
r'("[^"]+"|(#|@)[-_a-zA-Z0-9\.]+|http://[-_a-zA-Z0-9\./?&%#]+|(foaf:|tag:|gr:|sioc:|rdfs:|rdf:|skos:|owl:|dc:|dcterms:|rev:)[-_a-zA-Z0-9]+)'

	#parse all tweets and add to graph
		
	for tweet in tweets:
		# find all triples in the current tweet
		for triple in re.finditer(expression,tweet):
			match = triple.group()
			# print "MATCH: %s" % match
			s,dummy,match = match.partition(" ")
			p,dummy,o = match.partition(" ") # this trick makes sure that literals will not be split after their first space character
			logging.info("-->TWEET found: %s, %s, %s" % (s,p,o))
			# s, p, o contain triple parts as raw strings now
			subj = None
			pred = None
			obj = None
			
			# create subject
			if s.startswith("@"):
				subj = T_USERS[s[1:]]
				subj_type = "user"				
			elif s.startswith("#"):
				subj = T_TAGS[s[1:]]
				subj_type = "tag"
			else:
				subj = T_DATA[urllib.quote(s)]
				subj_type = "uri"
				
			# create predicate	
			if p=="=" or p == "sameas":
				# tags:	http://www.holygoat.co.uk/owl/redwood/0.1/tags/equivalentTag
				# other resources: owl:SameAs
				if subj_type=="tag":
					pred = TAG['equivalentTag']
					pred_type = "equivalentTag"
				elif subj_type=="user" or subj_type == "uri":
					pred = OWL['sameAs']
					pred_type = "sameas"
					
			elif p=="subtag" and subj_type == "tag":
				# +skos:broader: A triple <A> skos:broader <B> asserts that <B>, the object of the triple, is a broader concept than <A>, the subject of the triple. 
				# http://www.w3.org/2004/02/skos/core#								
				pred = SKOS['broader']
				pred_type = "broader"
				
			elif p=="a":							
				pred = RDF['type']
				pred_type = "type"
				
			elif p.startswith("&gt;"):
				pred = T_PROPS[p[4:]]
				pred_type = "rdfprop"
				
			else:
				# CURIEs: (foaf:|tag:|gr:|sioc:|rdfs:|rdf:|skos:|owl:|dc:|dcterms:|rev:)
				for prefix, NS in curies:
					if p.startswith(prefix+":"):
						pred = NS[p[len(prefix)+1:]]
						pred_type = "curie"
				
				
			# create object / literal	
			if o.startswith("@"):
				obj = T_USERS[o[1:]]
				obj_type = "user"
								
			elif o.startswith("#"):
				obj = T_TAGS[o[1:]]
				obj_type = "tag"
								
			elif o.startswith("http://"):
				obj = T_DATA[urllib.quote(o)]
				obj_type = "uri"
							
			elif o.startswith('"'):
				o = o[1:-1] # cut off quotation marks
				obj = rdflib.Literal(o)
				obj_type = "literal"
			
			else:
				# CURIEs: (foaf:|tag:|gr:|sioc:|rdfs:|rdf:|skos:|owl:|dc:|dcterms:|rev:)
				for prefix, NS in curies:
					if o.startswith(prefix+":"):
						obj = NS[o[len(prefix)+1:]]
						obj_type = "curie"																	
				

			# sanity checks
			# sameas only between object of the same type
			# broader only between tags
			# type only for users or uris as subjects and uris or curies as objects
			# subj_types have already been checked
			
			# four elifs more readable than one huge condition :-)
			
			if subj != None and pred != None and obj != None:
				
				if (pred_type == "sameas" and (obj_type=="user" or obj_type == "uri")):
					g.add((subj,pred,obj)) # add triple to graph
				elif ((pred_type == "broader" or pred_type == "equivalentTag") and obj_type == "tag"):
					g.add((subj,pred,obj)) # add triple to graph
				elif (pred_type == "type" and (subj_type == "user" or subj_type == "uri") and (obj_type == "user" or obj_type == "uri")):
					g.add((subj,pred,obj)) # add triple to graph
				elif (pred_type == "rdfprop" or pred_type == "curie"):
					g.add((subj,pred,obj)) # add triple to graph
				
				if subj_type == "user":
					g.add((subj,RDF['type'],FOAF['Agent']))
				elif subj_type == "tag":
					g.add((subj,RDF['type'],TAG['Tag']))
					g.add((subj,TAG['name'],rdflib.Literal(s[1:]))) # cut off hash
					
				elif subj_type == "uri": # we do not make statements about http URIs directly, but create novel ones and link back to the original via foaf:topic
					g.add((subj,FOAF['topic'],rdflib.URIRef(s)))	
									
				if pred_type == "rdfprop":
					g.add((pred,RDF['type'],RDF['Property']))
									
				if obj_type == "user":
					g.add((obj,RDF['type'],FOAF['Agent']))
				elif obj_type == "tag":
					g.add((obj,RDF['type'],TAG['Tag']))
					g.add((obj,TAG['name'],rdflib.Literal(o[1:]))) # cut off hash
				elif obj_type == "uri":
					# we do not make statements about http URIs directly, but create novel ones and link back to the original via foaf:topic
					g.add((obj,FOAF['topic'],rdflib.URIRef(o)))			
										
	# when done, return graph
	return g
	
def expand_query(query,graph):
	"""
	expand_query(query,graph)
		expands the original query string by 
		1. building a map of hashtag and username alignment statements from the tweets from the social network
		2. replacing all hashtags and usernames by (hashtag OR synonym OR subtag) or (username OR alias1 OR alias2)
		format: {""|".atom"|".json"}
		
	"""	
	# don't forget to add @ and # !!!
	g = graph

	q2 = query # don't change variable used in the loop
		
#	logging.info("GRAPH: "+g.serialize())
	
	# step 1: find all hashtags and expand them 	
	for hashtag in re.finditer(r'#[-_a-zA-Z0-9\.]+',query):
		extension = ""
		# for all hashtags in the query, look for equivalent tags in the graph
		hashtag = hashtag.group() # convert regex match to string
		ht = g.objects(T_TAGS[hashtag[1:]], TAG['equivalentTag'])
		
		# compile extension
		for tag in ht:	# for each equivalent tag
			extension += (" OR #" + str(g.value(tag,TAG['name']))) # 
			
		# for all hashtags in the query, look for more specific tags in the graph
		subtags = g.subjects(SKOS['broader'], T_TAGS[hashtag[1:]])

		# compile extension
		for tag in subtags:	# for each subtag
			extension += (" OR #" + str(g.value(tag,TAG['name']))) #

		# compile extension
		for tag in ht:	# for each equivalent tag
			extension += (" OR #" + str(g.value(tag,TAG['name']))) #	
			
		q2 = q2.replace(hashtag, hashtag+extension) # expand "#munich to #munich OR #muenchen"
		
	# step 2: find all user ids and expand them 
	for user in re.finditer(r'@[-_a-zA-Z0-9\.]+',query):
		extension = ""		
		user = user.group() # convert regex match to string		
		
		# for all user ids in the query, look for equivalent user ids in the graph
		users = g.objects(T_USERS[user[1:]], OWL['sameAs'])
				
		# compile extension
		for u in users:	# for each equivalent user id
			u = str(u)
			u = u.replace(str(T_USERS),"") # get local part of user
			extension += (" OR @" + u) 
			 
		q2 = q2.replace(user, user+extension) # expand "@mhepp to @mhepp OR @mfhepp"
						
	logging.info(" QUERY:%s, EXPANDED QUER> %s" % (query, q2))	
	
	return q2
		
def getText(nodelist):
	"""
	getText(nodelist)
	Helper method to extract all text content of all xml subnodes (taken from the Python doc)
	"""
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc = rc + node.data
	return rc

