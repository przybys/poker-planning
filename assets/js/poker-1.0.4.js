(function($) {
	
	var Poker = function(element) {
		this.$game = null;
		this.me = null;
		this.token = null;
		this.myEstimates = {};
		this.game = null;
		
		this.init(element);
	};
	
	Poker.VERSION = '1.0.2';
	
	Poker.prototype.init = function(element) {
		this.$game = $(element);
		this.gameUrl = this.$game.data('url');
		this.me = this.$game.data('me');
		this.token = this.$game.data('token');
		
		this.setup();
		
		this.openChannel();
	};
	
	Poker.prototype.setup = function() {
		this.selectUrl();
		this.submitForm();
		this.tooltips();
		this.clickLinks();
		this.clickCards();
	};
	
	Poker.prototype.selectUrl = function() {
		this.$game.on('click', '[data-game="url"]', function() {
			$(this).select();
		});
	};
	
	Poker.prototype.submitForm = function() {
		this.$game.on('submit', 'form', function(e) {
			var $form = $(this);
			var $btn = $form
				.find('.btn-primary')
				.button('loading');
			var settings = {
				url: $form.attr('action'),
				type: $form.attr('method'),
				data: $form.serialize()
			};
			
			$.ajax(settings).always(function() {
				$btn.button('reset');
				$form.trigger('reset');
			});
			
			e.preventDefault();
			
			return false;
		});
	};
	
	Poker.prototype.tooltips = function() {
		this.$game.tooltip({
			selector: '[data-toggle="tooltip"]',
			container: 'body'
		});
	};
	
	Poker.prototype.clickLinks = function() {
		this.$game.on('click', 'a.btn, .dropdown-menu a', function(e) {
			var $a = $(this);
			var settings = {
				url: $a.attr('href'),
				type: 'post'
			};
			
			$.ajax(settings);
			
			e.preventDefault();
			
			return false;
		});
	};
	
	Poker.prototype.clickCards = function() {
		this.$game.on('click', '[data-card]', $.proxy(this.myEstimate, this));
	};
	
	Poker.prototype.myEstimate = function(e) {
		var $a = $(e.target);
		var roundId = $a.closest('[data-round]').data('round');
		var card = $a.data('card');
		
		this.myEstimates[roundId] = card;
		
		e.preventDefault();
		
		return false;
	};
	
	Poker.prototype.openChannel = function() {
		var token = this.token;
		var channel = new goog.appengine.Channel(token);
		var handler = {
			'onopen': $.proxy(this.onOpened, this),
			'onmessage': $.proxy(this.onMessage, this),
			'onerror': $.proxy(this.onError, this),
			'onclose': function() {}
		};
		var socket = channel.open(handler);
		
		socket.onopen = $.proxy(this.onOpened, this);
		socket.onmessage = $.proxy(this.onMessage, this);
		socket.onerror = $.proxy(this.onError, this);
	};
	
	Poker.prototype.onOpened = function() {
		$.post(this.gameUrl + '/opened', $.proxy(this.initMyEstimates, this));
	};
	
	Poker.prototype.initMyEstimates = function(data) {
		this.myEstimates = data.estimates;
	};
	
	Poker.prototype.onMessage = function(message) {
		this.game = $.parseJSON(message.data);
		
		this.updateGame();
	};
	
	Poker.prototype.onError = function() {
		window.location.href = this.gameUrl;
	};
	
	Poker.prototype.updateGame = function() {
		this.updateStories();
		this.gameActions();
		this.updateParticipants();
	};
	
	Poker.prototype.updateStories = function() {
		var $stories = this.$game.find('[data-game="stories"]');
		
		$('.tooltip').detach();
		
		$stories.empty();
		this.clearSum();
		
		if(this.game.stories.length == 0) {
			$('<p>')
				.text(this.me != this.game.user
					? 'No stories? Just wait. There will be a story to estimate!'
					: 'Shall we play a game? Add a story!')
				.appendTo($stories);
		}
		
		for(var key in this.game.stories) {
			this.updateStory(this.game.stories[key], $stories);
		}
		
		if(!this.game.completed) {
			$('html, body').animate({
				scrollTop: $(document).height()
			});
		}
	};
	
	Poker.prototype.clearSum = function() {
		var $sum = this.$game.find('[data-game="sum-of-estimates"]');
		
		$sum.text('');
	};
	
	Poker.prototype.updateStory = function(story, $stories) {
		var template = '<div class="list-group-item"><span class="badge" data-toggle="tooltip" title="Story estimate"></span><h4 class="list-group-item-heading"></h4></div>';
		var $story = $(template)
			.attr('data-story', story.id)
			.attr('data-current', story.is_current)
			.find('.badge')
				.text(story.estimate == null ? '-' : (story.estimate < 0 ? 'Skipped' : story.estimate))
			.end()
			.find('.list-group-item-heading')
				.html(story.name)
			.end()
			.appendTo($stories);
		
		if(story.is_current) {
			if(story.estimate == null) {
				this.updateRounds(story.rounds, $story);
			}
			
			this.storyActions(story, $story);
		}
		
		this.addToSum(story);
	};
	
	Poker.prototype.addToSum = function(story) {
		var $sum = this.$game.find('[data-game="sum-of-estimates"]');
		
		var sum = parseInt($sum.text(), 10);
		
		if(isNaN(sum)) {
			sum = 0;
		}
		
		var estimate = parseInt(story.estimate, 10);
		
		if(isNaN(estimate)) {
			estimate = 0;
		}
		
		if(estimate > 0) {
			$sum.html(sum + estimate);
		}
	};
	
	Poker.prototype.storyActions = function(story, $story) {
		if(this.me != this.game.user) {
			return;
		}
		
		$('<hr>')
			.appendTo($story);
		
		var template = '<div data-game="story-actions" class="btn-group btn-group-sm dropup" role="group"></div>';
		
		var $actions = $(template)
			.appendTo($story);
		
		$('<a class="btn btn-primary"></a>')
			.attr('href', story.url + '/round')
			.append('<span class="glyphicon glyphicon-plus"></span> New round')
			.appendTo($actions);
		
		var $complete = $('<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown"></button>')
			.append('<span class="glyphicon glyphicon-ok"></span> Complete story <span class="caret"></span>');
		
		var $menu = $('<ul class="dropdown-menu" role="menu"></ul>');
		
		for(var index in this.game.deck) {
			var $item = $('<li>')
				.appendTo($menu);
			
			$('<a>')
				.attr('href', story.url + '/complete?card=' + index)
				.text(this.game.deck[index])
				.appendTo($item);
		}
		
		$('<div class="btn-group btn-group-sm"></div>')
			.append($complete)
			.append($menu)
			.appendTo($actions);
		
		$('<a class="btn btn-primary"></a>')
			.attr('href', story.url + '/skip')
			.append('<span class="glyphicon glyphicon-step-forward"></span> Skip story')
			.appendTo($actions);
	};
	
	Poker.prototype.updateRounds = function(rounds, $story) {
		var template = '<ol data-game="rounds" class="list-unstyled"></ol>';
		var $rounds = $(template)
			.appendTo($story);
		
		for(var key in rounds) {
			this.updateRound(rounds[key], $rounds);
		}
	};
	
	Poker.prototype.updateRound = function(round, $rounds) {
		var $round = $('<li>')
			.attr('data-round', round.id)
			.appendTo($rounds);
		
		$('<hr>')
			.appendTo($round);
		
		if(round.completed) {
			this.roundResults(round, $round);
		} else {
			this.estimateRound(round, $round);
		}
	};
	
	Poker.prototype.estimateRound = function(round, $round) {
		var template = '<div class="btn-group btn-group-lg" role="group"></div>';
		var $cards = $(template)
			.appendTo($round);
		var myEstimate = round.id in this.myEstimates ? this.myEstimates[round.id] : null;
		var participant = this.getParticipant(this.me);
		var observer = participant != null && participant.observer;
		var disabled = myEstimate != null || observer;
		
		if(observer) {
			$cards
				.attr('data-toggle', 'tooltip')
				.attr('data-placement', 'right')
				.attr('title', 'You can only observe');
		}
		
		for(var index in this.game.deck) {
			$('<a class="btn"></a>')
				.addClass(myEstimate == index ? 'btn-primary' : 'btn-default')
				.attr('data-card', index)
				.attr('href', round.url + '/estimate?card=' + index)
				.attr('disabled', disabled)
				.text(this.game.deck[index])
				.appendTo($cards);
		}
		
		this.waitingFor(round, $round);
		
		if(this.me == this.game.user) {
			$('<a class="btn btn-primary" data-toggle="tooltip" data-placement="right" data-container="body" title="Complete round"><span class="glyphicon glyphicon-ok"></span></a>')
				.attr('href', round.url + '/complete')
				.appendTo($cards);
		}
	};
	
	Poker.prototype.getParticipant = function(user) {
		for(var i in this.game.participants) {
			participant = this.game.participants[i];
			
			if(participant.user == user) {
				
				return participant;
			}
		}
		
		return null;
	};
	
	Poker.prototype.waitingFor = function(round, $round) {
		var template = '<ul class="list-inline" data-game="waiting-for"><li><strong>Waiting for:</strong></li></ul>';
		var $waitingFor = $(template)
			.appendTo($round);
		var participant = null;
		var estimate = null;
		var found = false;
		
		for(var i in this.game.participants) {
			participant = this.game.participants[i];
			found = false;
			
			for(var j in round.estimates) {
				estimate = round.estimates[j];
				
				if(participant.user == estimate.user) {
					
					found = true;
				}
			}
			
			if(found) {
				
				continue;
			}
			
			if(participant.observer) {
				
				continue;
			}
			
			var $item = $('<li>')
				.appendTo($waitingFor);
			
			if(participant.user == this.me) {
				$('<strong></strong>').text('You!').appendTo($item);
			} else {
				$('<small></small>').text(participant.name).appendTo($item);
			}
		}
	};
	
	Poker.prototype.roundResults = function(round, $round) {
		var estimate = null;
		var card = null;
		var $estimate = null;
		var participant = null;
		var name = null;
		var photo = null;
		var $card = null;
		var $sum = null;
		
		if(round.estimates.length == 0) {
			$round.addClass('hidden');
		}
		
		for(var index in this.game.deck) {
			card = this.game.deck[index];
			
			$estimate = $('<ul class="list-inline"></ul>')
				.addClass('card-results')
				.addClass('hidden')
				.attr('data-card', card)
				.appendTo($round);
			
			$card = $('<button type="button" class="btn btn-default" disabled="disabled"></button>')
				.text(card);
			
			$('<li>')
				.append($card)
				.appendTo($estimate);
			
			$sum = $('<span>')
				.addClass('label')
				.addClass('label-default')
				.attr('data-toggle', 'tooltip')
				.attr('title', 'Sum of card estimates')
				.attr('data-card', 'sum-of-estimates');
			
			$('<li>')
				.addClass('pull-right')
				.addClass('sum-of-estimates')
				.append($sum)
				.appendTo($estimate);
		}
		
		for(var key in round.estimates) {
			estimate = round.estimates[key];
			
			$estimate = $round
				.find('[data-card="' + estimate.card + '"]')
				.removeClass('hidden');
			
			participant = this.getParticipant(estimate.user);
			
			if(participant != null) {
				photo = participant.photo;
				name = participant.name;
			} else {
				photo = null;
				name = estimate.name;
			}
			
			var $photo = $('<img>')
				.addClass('img-rounded')
				.attr('src', photo)
				.attr('alt', name)
				.attr('width', 34)
				.attr('height', 34)
				.attr('data-toggle', 'tooltip')
				.attr('title', name);
			
			$('<li></li>')
				.append($photo)
				.appendTo($estimate);
			
			$sum = $estimate
				.find('[data-card="sum-of-estimates"]');
			
			var sum = parseInt($sum.text(), 10);
			
			if(isNaN(sum)) {
				sum = 0;
			}
			
			$sum.text(sum + 1);
		}
	};
	
	Poker.prototype.gameActions = function() {
		if(this.me != this.game.user) {
			return;
		}
		
		var $actions = this.$game.find('[data-game="actions"]');
		var $story = $actions.find('[data-game="story"] input, [data-game="story"] button');
		var $complete = $actions.find('[data-game="complete"]');
		var $reopen = $actions.find('[data-game="reopen"]');
		
		if(this.game.current_story) {
			$actions.addClass('hidden');
		} else {
			$actions.removeClass('hidden');
		}
		
		if(this.game.completed) {
			$story.prop('disabled', true);
			$complete.addClass('hidden');
			$reopen.removeClass('hidden');
		} else {
			$story.prop('disabled', false);
			$complete.removeClass('hidden');
			$reopen.addClass('hidden');
			
			$story
				.filter(':first')
				.focus();
		}
	};
	
	Poker.prototype.updateParticipants = function() {
		var $participants = this.$game
			.find('[data-game="participants"]')
			.empty();
		var participant = null;
		
		for(var key in this.game.participants) {
			participant = this.game.participants[key];
			
			var $icon = $('<span class="glyphicon"></span>')
				.addClass(participant.observer ? 'glyphicon-eye-open' : 'glyphicon-user')
				.attr('data-toggle', 'tooltip')
				.attr('title', participant.observer ? 'Game observer' : 'Game player');
			
			var $photo = $('<img>')
				.addClass('img-rounded')
				.attr('src', participant.photo)
				.attr('alt', participant.name)
				.attr('width', 34)
				.attr('height', 34);
			
			if(this.me == this.game.user) {
				
				var $options = $('<span class="glyphicon"></span>')
					.addClass('glyphicon-option-horizontal');
				
				var $toggle = $('<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown"></button>')
					.append($options);
				
				var $menu = $('<ul class="dropdown-menu" role="menu"></ul>');
				
				this.toggleObserver(participant, $menu);
				this.deleteParticipant(participant, $menu);
				
				var $dropdown = $('<div class="btn-group">')
					.addClass('pull-right')
					.append($toggle)
					.append($menu);
				
				$('<li>')
					.data('user', participant.user)
					.append($photo)
					.append(' ')
					.append(participant.name)
					.append(' ')
					.append($icon)
					.append(' ')
					.append($dropdown)
					.appendTo($participants);
				
			} else {
				
				$('<li>')
					.data('user', participant.user)
					.append($photo)
					.append(' ')
					.append(participant.name)
					.append(' ')
					.append($icon)
					.appendTo($participants);
			}
		}
	};
	
	Poker.prototype.deleteParticipant = function(participant, $menu) {
		if(this.game.user == participant.user) {
			return;
		}
		
		var action = '/delete';
		var icon = 'glyphicon-trash';
		var text = 'Delete participant';
		
		var $item = $('<li>')
			.appendTo($menu);
		
		var $icon = $('<span class="glyphicon"></span>')
			.addClass(icon);
		
		$('<a>')
			.attr('href', participant.url + action)
			.append($icon)
			.append(' ')
			.append(text)
			.appendTo($item);
	};
	
	Poker.prototype.toggleObserver = function(participant, $menu) {
		
		var action = '/observer';
		var icon = 'glyphicon-eye-open';
		var text = 'Make game observer';
		
		if(participant.observer) {
			action = '/player';
			icon = 'glyphicon-user';
			text = 'Make game player';
		}
		
		var $item = $('<li>')
			.appendTo($menu);
		
		var $icon = $('<span class="glyphicon"></span>')
			.addClass(icon);
		
		$('<a>')
			.attr('href', participant.url + action)
			.append($icon)
			.append(' ')
			.append(text)
			.appendTo($item);
	};
	
	function Plugin() {
		return this.each(function() {
			var $this = $(this);
			var data = $this.data('poker');
			
			if(!data) {
				data = new Poker(this);
				$this.data('poker', data);
			}
		});
	};
	
	$.fn.poker = Plugin;
	
	$(window).on('load', function() {
		$('[data-game="poker"]').each(function() {
			$(this).poker();
		});
	});
	
})(jQuery);
