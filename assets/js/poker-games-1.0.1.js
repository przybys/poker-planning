(function($) {
	
	var PokerGames = function(element) {
		this.$games = null;
		
		this.init(element);
	}
	
	PokerGames.VERSION = '1.0.1';
	
	PokerGames.prototype.init = function(element) {
		this.$games = $(element);
		
		this.setup();
	};
	
	PokerGames.prototype.setup = function() {
		this.newGame();
		this.tooltips();
	};
	
	PokerGames.prototype.newGame = function() {
		var $newGame = this.$games.find('[data-games="new-game"]');
		
		$newGame.on('show.bs.modal', function() {
			$newGame
				.find('form')
				.trigger('reset');
		});
		
		$newGame.on('shown.bs.modal', function() {
			$newGame
				.find('input[type="text"]')
				.filter(':first')
				.focus();
		});
		
		$newGame.find('form').submit(function(e) {
			var $form = $(this);
			var $btn = $newGame
				.find('.btn-primary')
				.button('loading');
		});
	};
	
	PokerGames.prototype.tooltips = function() {
		this.$games.tooltip({
			selector: '[data-toggle="tooltip"]',
			container: 'body'
		});
	};
	
	function Plugin() {
		return this.each(function() {
			var $this = $(this);
			var data = $this.data('poker-games');
			
			if(!data) {
				data = new PokerGames(this);
				$this.data('poker-games', data);
			}
		});
	};
	
	$.fn.pokerGames = Plugin;
	
	$(window).on('load', function() {
		$('[data-games="poker"]').each(function() {
			$(this).pokerGames();
		});
	});
	
})(jQuery);
