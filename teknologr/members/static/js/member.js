var changed = false;

$(document).ready(function() {
	$('#memberform').change(function(){
		changed = true;
	});

	$('#memberform').submit(function(){
		changed = false;
	});
});


$(window).on('beforeunload', function(){
	if(changed) {
		return "Changes not saved";
	}
});