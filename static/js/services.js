'use strict';

angular.module('angularFlaskServices', ['ngResource'])
	.factory('Search', function($resource){
		return $resource('/api/analyzer/', {}, {
			post: {
				method: 'POST',
			}
		})
	})
;



