'use strict';

/* Controllers */

function waitmessages()
{
	var securityquotes = [
		"The true computer hackers follow a certain set of ethics that forbids them to profit or cause harm from their activities.",
		"If you think technology can solve your security problems, then you don’t understand the problems and you don’t understand the technology.",
		"Passwords are like underwear: you don’t let people see it, you should change it very often, and you shouldn’t share it with strangers.",
		"If you spend more on coffee than on IT security, you will be hacked. What’s more, you deserve to be hacked.",
		"Most people don't know what a rootkit is. So why should they care about it?",
        "If you give a hacker a new toy, the first thing he'll do is take it apart to figure out how it works",
        "Social engineering has become about 75% of an average hacker's toolkit, and for the most successful hackers, it reaches 90% or more.",
        "Behind every successful  Coder there an even more successful De-coder to understand that code",
        "Software is like sex: it's better when it's free.",
        "Talk is cheap. Show me the code.",
        "Microsoft isn't evil, they just make really crappy operating systems.",
        "My name is Linus, and I am your God.",
        "A lot of Hacking is playing with other people, you know, getting them to do strange things ",
        " Is this real or is it a game?",
        "Then you'll see, that it is not the spoon that bends, it is only yourself.",
        "You have to let it all go, Neo. Fear, doubt, and disbelief. Free your mind.",
        "Hasta la vista, baby."
	]
	var quote = securityquotes[Math.floor(Math.random() * securityquotes.length)];
    return quote;
}

function SearchController($scope, Search, $window, $timeout){
    $scope.analyze = function(url, previous) {
    	var expression = /[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?/gi;
		var regex = new RegExp(expression);

    	if (url!=undefined && url!='' && url.match(regex))
    	{
    		Search.post({url: url, previous: previous}, function(data) {
    			$window.location = '/result/' + data.id;
    		});
    	}
    	else
    	{
    		alert('Please enter a GitHub URL');
    	}

    }
}

function ResultController($scope, $routeParams, $timeout, Result)
{
	var queryResults = Result.get({queue_id: $routeParams.queue_id}, function(data) {
        $scope.data = data;
    });

    function tick() {
        $scope.quote = waitmessages();
        var queryResults = Result.get({queue_id: $routeParams.queue_id}, function(data) {
            $scope.data = data;
            if ($scope.data.status!='inprocess')
            {
                $timeout.cancel(timer);
            }
            var timer  = $timeout(tick, 3000);
        });
    }

    var timer  = $timeout(tick, 3000);
    $scope.$on("$destroy", function() {
        if (timer) {
            $timeout.cancel(timer);
        }
    });
}

