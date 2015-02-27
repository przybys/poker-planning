#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import webapp2

from poker.handlers import *

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/game', NewGame),
    ('/game/(\d+)', GamePage),
    ('/game/(\d+)/opened', GameOpened),
    ('/game/(\d+)/(complete|reopen)', ToggleCompleteGame),
    ('/game/(\d+)/delete', DeleteGame),
    ('/game/(\d+)/story', NewStory),
    ('/game/(\d+)/story/(\d+)/skip', SkipStory),
    ('/game/(\d+)/story/(\d+)/complete', CompleteStory),
    ('/game/(\d+)/story/(\d+)/round', NewRound),
    ('/game/(\d+)/story/(\d+)/round/(\d+)/complete', CompleteRound),
    ('/game/(\d+)/story/(\d+)/round/(\d+)/estimate', EstimateRound),
    ('/game/(\d+)/participant/(\d+)/(player|observer)', ToggleGameObserver),
], debug = True)
