var changed = false;

$(document).ready(function() {

	// Buttons for adding items to the selected member
	// XXX: Could probably be combined
	add_request_listener({
		selector: "#add-do-form",
		method: "POST",
		url: "/api/decorationownerships/",
	});
	add_request_listener({
		selector: "#add-f-form",
		method: "POST",
		url: "/api/functionaries/",
	});
	add_request_listener({
		selector: "#add-gm-form",
		method: "POST",
		url: "/api/groupmemberships/",
	});
	add_request_listener({
		selector: "#add-mt-form",
		method: "POST",
		url: "/api/membertypes/",
	});

	$('.edit-mt-button').click(function(){
		const id = $(this).data("id");
		$("#edit-mt-modal .modal-body").load(`/admin/membertypes/${id}/form/`, () => {
			add_request_listener({
				selector: "#edit-mt-form",
				method: "PUT",
				url: `/api/membertypes/${id}/`,
			});

			$('#edit-mt-modal').modal();
		});
	});

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