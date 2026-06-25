$(document).ready(function () {
	// Update the decoration type
	add_request_listener({
		selector: "#edit-d-form",
		method: "PUT",
		url: element => `/api/decorations/${element.data("id")}/`,
	});
	// Delete the decoration type
	add_request_listener({
		selector: "#delete-d-button",
		method: "DELETE",
		url: element => `/api/decorations/${element.data("id")}/`,
		confirmMessage: "Vill du radera denna betygelse och alla dess betygelseinnehav?",
		newLocation: "/admin/decorations/",
	});

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
