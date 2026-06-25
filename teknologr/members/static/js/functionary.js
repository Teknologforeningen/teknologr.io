$(document).ready(function () {
	// Update the selected functionary type
	add_request_listener({
		selector: "#edit-ft-form",
		method: "PUT",
		url: element => `/api/functionarytypes/${element.data("id")}/`,
	});
	// Remove the selected functionary type
	add_request_listener({
		selector: "#delete-ft-button",
		method: "DELETE",
		url: element => `/api/functionarytypes/${element.data("id")}/`,
		confirmMessage: "Vill du radera denna post och alla dess postinnehav?",
		newLocation: "/admin/functionarytypes/",
	});

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
