'use strict';

/* Controllers */

function waitmessages($scope, $timeout)
{
	var quotey = function() {
		var securityquotes = [
			"The true computer hackers follow a certain set of ethics that forbids them to profit or cause harm from their activities.",
			"If you think technology can solve your security problems, then you don’t understand the problems and you don’t understand the technology.",
			"Passwords are like underwear: you don’t let people see it, you should change it very often, and you shouldn’t share it with strangers.",
			"If you spend more on coffee than on IT security, you will be hacked. What’s more, you deserve to be hacked."
		]
		var quote = securityquotes[Math.floor(Math.random() * securityquotes.length)];
		$scope.quote = quote;
		timer = $timeout(quotey, 3000);
	}

	var timer = $timeout(quotey, 50);

	$scope.$on("$destroy", function() {
        if (timer) {
            $timeout.cancel(timer);
        }
    });

}

function SearchController($scope, Search, $window, $timeout){
    $scope.analyze = function(url) {
    	var expression = /[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?/gi;
		var regex = new RegExp(expression);

    	if (url!=undefined && url!='' && url.match(regex))
    	{
    		Search.post({url: url}, function(data) {
    			window.localStorage.setItem('data', JSON.stringify(data));
    			$window.location = '/result';
    		});
    		waitmessages($scope, $timeout);
    	}
    	else
    	{
    		alert('Please enter a URL');
    	}

    }
}

function ResultController($scope)
{
	$scope.data  = JSON.parse(window.localStorage.getItem('data'));
	console.log($scope.data);
}

