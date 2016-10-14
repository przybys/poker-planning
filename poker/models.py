#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import json
import datetime

from jinja2.utils import urlize

from google.appengine.ext import db
from google.appengine.api import channel

__all__ = [
    'Game',
    'Participant',
    'Story',
    'Round',
    'Estimate',
]

class Game(db.Model):
    DECK_CHOICES = (
        (1 , ('1', '2', '3', '5', '8', '13', '21', '100', '?', 'Coffee')),
        (2 , ('0', '1/2' , '1', '2', '3', '5', '8', '13', '20', '40', '60', '100', '?', 'oo')),
        (3 , ('0', '1', '2', '3', '5', '8', '13', '21', '44', '?', 'oo')),
    )
    name = db.StringProperty(required = True)
    deck = db.IntegerProperty(required = True, choices = [deck[0] for deck in DECK_CHOICES])
    completed = db.BooleanProperty(default = False)
    user = db.UserProperty(required = True)
    current_story_id = db.IntegerProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    
    def get_deck(self):
        for deck in self.DECK_CHOICES:
            if self.deck == deck[0]:
                return deck[1]
        return ()
    
    def get_participants(self):
        return Participant.all().ancestor(self).order("created")
    
    def get_stories(self):
        return Story.all().ancestor(self).order("created")
    
    def get_url(self):
        game_url = '/game/' + str(self.key().id())
        return game_url
    
    def get_current_story(self):
        if not self.current_story_id:
            return None
        return Story.get_by_id(self.current_story_id, self)
    
    def get_participant_messages(self):
        messages = []
        for participant in self.get_participants():
            message = participant.get_message()
            messages.append(message)
        return messages
    
    def get_story_messages(self):
        messages = []
        for story in self.get_stories():
            message = story.get_message()
            messages.append(message)
        return messages
    
    def get_current_story_message(self):
        current_story = self.get_current_story()
        if not current_story:
            return None 
        return current_story.get_message()
    
    def get_message(self):
        message = {
            'id': self.key().id(),
            'name': self.name,
            'deck': self.get_deck(),
            'completed': self.completed,
            'user': self.user.user_id(),
            'current_story': self.get_current_story_message(),
            'url': self.get_url(),
            'participants': self.get_participant_messages(),
            'stories': self.get_story_messages(),
        }
        return message
    
    def send_update(self, force = True, user = None):
        message = self.get_message()
        message = json.dumps(message)
        participants = self.get_participants()
        for participant in participants:
            if user and participant.user == user:
                force = True
            participant.send_update(message, force)
    
    def get_user_estimates(self, user):
        estimates = {}
        if not user:
            return estimates
        for story in self.get_stories():
            for round in story.get_rounds():
                estimate = round.get_estimate(user)
                round_id = round.key().id()
                if estimate:
                    card = estimate.card
                    estimates[round_id] = card
        return estimates
    
    def delete(self, **kwargs):
        db.delete(Participant.all(keys_only = True).ancestor(self))
        stories = self.get_stories()
        for story in stories:
            story.delete()
        super(Game, self).delete(**kwargs)

class Participant(db.Model):
    user = db.UserProperty(required = True)
    name = db.StringProperty()
    photo = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    observer = db.BooleanProperty(required = True, default = False)
    last_update = db.DateTimeProperty(auto_now_add = True)
    
    def get_url(self):
        game_url = self.parent().get_url()
        participant_url = game_url + '/participant/' + self.key().name()
        return participant_url
    
    def get_name(self):
        if self.name:
            return self.name
        else:
            return self.user.nickname()
    
    def get_message(self):
        message = {
            'user': self.user.user_id(),
            'name': self.get_name(),
            'photo': self.photo,
            'observer': self.observer,
            'url': self.get_url()
        }
        return message
    
    def send_update(self, message, force):
        if force or self.need_update():
            self.last_update = datetime.datetime.now()
            self.put()
            channel.send_message(self.key().name(), message)
    
    def need_update(self):
        return datetime.datetime.now() - self.last_update > datetime.timedelta(seconds = 1)

class Story(db.Model):
    SKIPPED = -1
    name = db.StringProperty(required = True)
    estimate = db.IntegerProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    
    def get_rounds(self):
        return Round.all().ancestor(self).order("created")
    
    def get_estimate(self):
        game = self.parent()
        deck = game.get_deck()
        card = self.estimate
        if card == self.SKIPPED:
            return card
        if card is None:
            return None
        try:
            estimate = deck[card]
        except IndexError:
            return None
        return estimate
    
    def get_name_display(self):
        return urlize(self.name, 80)
    
    def get_url(self):
        game_url = self.parent().get_url()
        story_url = game_url + '/story/' + str(self.key().id())
        return story_url
    
    def is_current(self):
        game = self.parent()
        is_current = game.current_story_id == self.key().id()
        return is_current
    
    def new_round(self):
        rounds = self.get_rounds()
        for round in rounds:
            round.completed = True
            round.put()
        round = Round(
            parent = self
        )
        round.put()
        self.estimate = None
        self.put()
        return round
    
    def get_round_messages(self):
        messages = []
        if not self.is_current():
            return messages
        for round in self.get_rounds():
            message = round.get_message()
            messages.append(message)
        return messages
    
    def get_message(self):
        message = {
            'id': self.key().id(),
            'name': self.get_name_display(),
            'estimate': self.get_estimate(),
            'url': self.get_url(),
            'is_current': self.is_current(),
            'rounds': self.get_round_messages(),
        }
        return message
    
    def delete(self, **kwargs):
        rounds = self.get_rounds()
        for round in rounds:
            round.delete()
        super(Story, self).delete(**kwargs)

class Round(db.Model):
    completed = db.BooleanProperty(default = False)
    created = db.DateTimeProperty(auto_now_add = True)
    
    def get_estimates(self):
        return Estimate.all().ancestor(self).order("created")
    
    def get_url(self):
        story_url = self.parent().get_url()
        round_url = story_url + '/round/' + str(self.key().id())
        return round_url
    
    def get_estimate(self, user):
        if not user:
            return None
        estimate_key = str(self.key().id()) + str(user.user_id())
        estimate = Estimate.get_by_key_name(estimate_key, self)
        return estimate
    
    def get_estimate_messages(self):
        messages = []
        for estimate in self.get_estimates():
            message = estimate.get_message()
            messages.append(message)
        return messages
    
    def get_message(self):
        message = {
            'id': self.key().id(),
            'completed': self.completed,
            'url': self.get_url(),
            'estimates': self.get_estimate_messages(),
        }
        return message
    
    def delete(self, **kwargs):
        db.delete(Estimate.all(keys_only = True).ancestor(self))
        super(Round, self).delete(**kwargs)

class Estimate(db.Model):
    user = db.UserProperty(required = True)
    card = db.IntegerProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    
    def get_message(self):
        message = {
            'user': self.user.user_id(),
            'name': self.user.nickname(),
            'card': self.get_card(),
        }
        return message
    
    def get_card(self):
        round = self.parent()
        if not round.completed:
            return None
        story = round.parent()
        game = story.parent()
        deck = game.get_deck()
        card = self.card
        try:
            estimate = deck[card]
        except IndexError:
            return None
        return estimate
