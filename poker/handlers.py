#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import datetime
import json
import webapp2
import jinja2

from google.appengine.api import users
from google.appengine.api import channel

from poker.models import *
from poker.oauth2 import decorator, service

JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates')),
    extensions = [
        'jinja2.ext.autoescape',
    ],
    autoescape = True
)

__all__ = [
    'MainPage',
    'NewGame',
    'GameList',
    'DeleteGame',
    'GamePage',
    'GameOpened',
    'ToggleCompleteGame',
    'NewStory',
    'SkipStory',
    'CompleteStory',
    'NewRound',
    'CompleteRound',
    'EstimateRound',
    'ToggleGameObserver',
    'DeleteParticipant',
]

class Player():
    user = None
    profile = None
    
    def __init__(self):
        user = users.get_current_user()
        if user:
            self.user = user
    
    def get_user(self):
        return self.user
    
    def get_url(self, dest_url):
        if self.user:
            return users.create_logout_url('/')
        return users.create_login_url(dest_url)
    
    def get_games(self):
        return Game.all().filter("user =", self.user)
    
    def get_profile(self):
        if not self.profile:
            try:
                http = decorator.http()
                self.profile = service.people().get(userId='me').execute(http=http)
            except Exception:
                pass
        return self.profile
    
    def get_name(self):
        profile = self.get_profile()
        if profile and 'displayName' in profile:
            return profile['displayName']
        return None
    
    def get_photo(self):
        profile = self.get_profile()
        if profile and 'image' in profile:
            return profile['image']['url']
        return None

class PokerRequestHandler(webapp2.RequestHandler):
    player = None
    
    def get_player(self):
        if self.player is None:
            player = Player()
        return player
    
    def get_user(self, abort = True):
        user = self.get_player().get_user()
        if abort:
            if not user:
                self.abort(401)
        return user
    
    def get_game(self, game_id, check_user = False):
        game = Game.get_by_id(int(game_id))
        if not game:
            self.abort(404)
        if check_user:
            user = self.get_player().get_user()
            if game.user != user:
                self.abort(403)
        return game
    
    def get_story(self, game_id, story_id, check_user = False):
        game = self.get_game(game_id, check_user)
        story = Story.get_by_id(int(story_id), game)
        if not story:
            self.abort(404)
        return story
    
    def get_round(self, game_id, story_id, round_id, check_user = False):
        story = self.get_story(game_id, story_id, check_user)
        round = Round.get_by_id(int(round_id), story)
        if not round:
            self.abort(404)
        return round
    
    def get_participant(self, game_id, participant_key, check_user = False):
        game = self.get_game(game_id, check_user)
        participant = Participant.get_by_key_name(str(participant_key), game)
        if not participant:
            self.abort(404)
        return participant

class MainPage(PokerRequestHandler):
    def get(self):
        player = self.get_player()
        user = player.get_user()
        if user:
            return self.redirect('/game/list')
        url = player.get_url(self.request.uri)
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({
            'user': user,
            'url': url,
            'now': datetime.datetime.now(),
        }))

class NewGame(PokerRequestHandler):
    def post(self):
        user = self.get_user()
        try:
            game = Game(
                name = self.request.get('name'),
                deck = int(self.request.get('deck')),
                user = user
            )
        except:
            return self.redirect('/')
        game.put()
        game_url = game.get_url()
        return self.redirect(game_url)

class GameList(PokerRequestHandler):
    
    @decorator.oauth_required
    def get(self):
        player = self.get_player()
        user = player.get_user()
        url = player.get_url(self.request.uri)
        games = player.get_games().order("-created")
        template = JINJA_ENVIRONMENT.get_template('list.html')
        self.response.write(template.render({
            'user': user,
            'player_name': player.get_name(),
            'player_photo': player.get_photo(),
            'url': url,
            'games': games,
            'decks': Game.DECK_CHOICES,
            'now': datetime.datetime.now(),
        }))

class DeleteGame(PokerRequestHandler):
    def get(self, game_id):
        game = self.get_game(game_id, check_user = True)
        game.delete()
        return self.redirect('/')

class GamePage(PokerRequestHandler):
    
    @decorator.oauth_required
    def get(self, game_id):
        user = self.get_user()
        player = self.get_player()
        url = player.get_url(self.request.uri)
        game = self.get_game(game_id)
        deck = json.dumps(game.get_deck())
        participant_key = str(game.key().id()) + str(user.user_id())
        participant = Participant.get_or_insert(
            participant_key,
            parent = game,
            user = user
        )
        if not participant.name or not participant.photo:
            participant.name = player.get_name()
            participant.photo = player.get_photo()
            participant.put()
        token = channel.create_channel(participant_key)
        template = JINJA_ENVIRONMENT.get_template('game.html')
        self.response.write(template.render({
            'user': user,
            'player_name': player.get_name(),
            'player_photo': player.get_photo(),
            'game': game,
            'deck': deck,
            'url': url,
            'now': datetime.datetime.now(),
            'request_url': self.request.url,
            'token': token,
        }))

class GameOpened(PokerRequestHandler):
    def post(self, game_id):
        user = self.get_user()
        game = self.get_game(game_id)
        game.send_update()
        response = {
            'estimates': game.get_user_estimates(user),
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(response))

class ToggleCompleteGame(PokerRequestHandler):
    def get(self, game_id, toggle):
        self.post(game_id, toggle)
        return self.redirect('/game/list')
    
    def post(self, game_id, toggle):
        game = self.get_game(game_id, check_user = True)
        game.completed = toggle == 'complete'
        if game.completed:
            for story in game.get_stories():
                for round in story.get_rounds():
                    round.completed = True
                    round.put()
                if story.estimate is None:
                    story.estimate = Story.SKIPPED
                    story.put()
        game.current_story_id = None
        game.put()
        game.send_update()

class NewStory(PokerRequestHandler):
    def post(self, game_id):
        game = self.get_game(game_id, check_user = True)
        current_story = game.get_current_story()
        if game.completed or current_story:
            self.abort(403)
        try:
            story = Story(
                parent = game,
                name = self.request.get('name')
            )
        except:
            self.abort(400)
        story.put()
        story.new_round()
        game.current_story_id = story.key().id()
        game.put()
        game.send_update()

class SkipStory(PokerRequestHandler):
    def post(self, game_id, story_id):
        story = self.get_story(game_id, story_id, check_user = True)
        rounds = story.get_rounds()
        for round in rounds:
            round.completed = True
            round.put()
        story.estimate = Story.SKIPPED
        story.put()
        game = story.parent()
        game.current_story_id = None
        game.put()
        game.send_update()

class CompleteStory(PokerRequestHandler):
    def post(self, game_id, story_id):
        story = self.get_story(game_id, story_id, check_user = True)
        game = story.parent()
        if game.completed or not story.is_current():
            self.abort(403)
        deck = game.get_deck()
        card = self.request.get('card')
        try:
            card = int(card)
        except ValueError:
            self.abort(400)
        try:
            estimate = deck[card]
        except IndexError:
            self.abort(400)
        rounds = story.get_rounds()
        for round in rounds:
            round.completed = True
            round.put()
        story.estimate = card
        story.put()
        game.current_story_id = None
        game.put()
        game.send_update()

class NewRound(PokerRequestHandler):
    def post(self, game_id, story_id):
        story = self.get_story(game_id, story_id, check_user = True)
        game = story.parent()
        if game.completed or not story.is_current():
            self.abort(403)
        story.new_round()
        game.send_update()

class CompleteRound(PokerRequestHandler):
    def post(self, game_id, story_id, round_id):
        round = self.get_round(game_id, story_id, round_id, check_user = True)
        story = round.parent()
        game = story.parent()
        if game.completed or not story.is_current():
            self.abort(403)
        round.completed = True
        round.put()
        game.send_update()

class EstimateRound(PokerRequestHandler):
    def post(self, game_id, story_id, round_id):
        round = self.get_round(game_id, story_id, round_id)
        user = self.get_user()
        story = round.parent()
        game = story.parent()
        if game.completed or not story.is_current() or round.completed:
            self.abort(403)
        deck = game.get_deck()
        card = self.request.get('card')
        try:
            card = int(card)
        except ValueError:
            self.abort(400)
        try:
            estimate = deck[card]
        except IndexError:
            self.abort(400)
        estimate_key = str(round.key().id()) + str(user.user_id())
        estimate = Estimate.get_or_insert(
            estimate_key,
            parent = round,
            user = user,
            card = card
        )
        estimate.put()
        count_participants = game.get_participants().filter('observer =', False).count()
        count_estimates = round.get_estimates().count()
        if count_participants == count_estimates:
            round.completed = True
            round.put()
        game.send_update(force = round.completed, user = user)

class ToggleGameObserver(PokerRequestHandler):
    def post(self, game_id, participant_key, observer):
        participant = self.get_participant(game_id, participant_key, check_user = True)
        participant.observer = observer == 'observer'
        participant.put()
        game = participant.parent()
        game.send_update()

class DeleteParticipant(PokerRequestHandler):
    def post(self, game_id, participant_key):
        participant = self.get_participant(game_id, participant_key, check_user = True)
        game = participant.parent()
        if game.user == participant.user:
            self.abort(403)
        participant.delete()
        game.send_update()
