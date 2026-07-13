$(document).ready(function () {
	// Copy the hidden list of emails to the clipboard
	$('#copy2clipboard').click(function(){
		$("#members_email_list").select();
		document.execCommand('copy');
	});

	add_ajax_multiselect_extension({
		selector_button: "#gmform-create-member",
		selector_input: "#gmform_member_text",
		selector_submit: "#gmform-submit-memberships",
	});
});
