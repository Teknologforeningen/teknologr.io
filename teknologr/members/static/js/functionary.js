$(document).ready(function () {
	// Add a person to the list
	add_request_listener({
		selector: "#add-f-form",
		method: "POST",
		url: `/api/multi-functionaries/`,
		confirmMessage: confirmMessageCreateMembers,
	});

	add_ajax_multiselect_extension({
		selector_button: "#fform-create-member",
		selector_input: "#fform_member_text",
		selector_submit: "#fform-submit-functionaries",
	});
});
