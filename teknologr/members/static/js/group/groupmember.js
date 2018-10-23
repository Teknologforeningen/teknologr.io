$(document).ready(function() {

	$("#addgroupmemberform").submit(function(event){
		var data = $(this).serialize();
		var request = $.ajax({
			url: "/api/multiGroupMembership/",
			method: "POST",
			data: data
		});

		request.done(function() {
			location.reload();
		});

		request.fail(function( jqHXR, textStatus ){
			alert( "Request failed: " + textStatus + ": " + jqHXR.responseText );
		});

		event.preventDefault();
	});

	$(".removeMembership").click(function(){
		if(confirm("Vill du ta bort detta gruppmedlemskap?")) {		
			var id = $(this).data('id');	

			var request = $.ajax({
				url: "/api/groupMembership/" + id + "/",
				method: "DELETE"
			})

			request.done(function() {
				location.reload();
			});

			request.fail(function( jqHXR, textStatus ){
				alert( "Request failed: " + textStatus + ": " + jqHXR.responseText );
			});
		}
	});
	$('#copy2clipboard').click(function(){
		$("textarea").select();
    document.execCommand('copy');
	});
});
