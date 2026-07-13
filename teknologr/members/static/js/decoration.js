$(document).ready(function () {
	// Add a person to the list
	add_request_listener({
		selector: "#add-do-form",
		method: "POST",
		url: "/api/multi-decorationownerships/",
		confirmMessage: confirmMessageCreateMembers,
	});

	add_ajax_multiselect_extension({
		selector_button: "#doform-create-member",
		selector_input: "#doform_member_text",
		selector_submit: "#doform-submit-ownerships",
	});
});
