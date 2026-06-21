// Sidebar ajax search delay timer
var timer;

/**
 * Helper method for calling a function, if it is a function.
 */
const call_if_function = (fn, ...params) => {
	return typeof fn === "function" ? fn(...params) : fn;
}

/**
 * Helper function for adding a listener to an element that does a request.
 *
 * @param {Object} options
 * @param {String} option.element          The element(s) to add the listener to
 * @param {String} option.method           The request method
 * @param {String} option.url              The request url
 * @param {Object} [option.data]           The request data (default: Element.serialize())
 * @param {String} [option.confirmMessage] An optional confirm message
 * @param {String} [option.newLocation]    The url to redirect to after the request is done (default: reload current page)
 *
 * Some of the options also allow a function (e: Element) => T to be passed, if the option value depends on for example data on the specific element. These options are:
 * @param {String | (e: Element) => String} option.url
 * @param {Object | (e: Element) => Object} dption.data
 * @param {String | (e: Element) => String} option.confirmMessage
 * @param {String | (e: Element, msg: Any) => String} option.newLocation
 */
const add_request_listener = ({ selector, method, url, data, confirmMessage, newLocation }) => {
	// Get the element(s) to attach the listener to
	$(selector).each((_, domElement) => {
		// Deduce what to listen for based on the element tag
		const type = domElement.tagName.toLowerCase() === "form" ? "submit" : "click";

		const e = $(domElement);
		// Add a listener to the element
		e.on(type, event => {
			event.preventDefault();
			event.stopPropagation();

			const msg = call_if_function(confirmMessage, e);
			if (msg && !confirm(msg)) return;

			// Do the request
			const request = $.ajax({
				method,
				url: call_if_function(url, e),
				data: data ? call_if_function(data, e) : e.serialize(),
			});

			// Add listeners to the request
			request.done(msg => {
				if (newLocation) window.location = call_if_function(newLocation, e, msg);
				else location.reload();
			});
			// XXX: The error message is not very helpful for the user, so should probably change this to something else
			request.fail((jqXHR, textStatus, errorThrown) => {
				alert(`Request failed with status ${jqXHR.status} (${jqXHR.statusText}): ${jqXHR.responseText}`);
			});
		});
	});
}

/**
 * Extend the functionality of the AutoCompleteSelectMultipleField from django-ajax-selects by also allowing new members to be created simultaneously. This is how it's done:
 * 1. Add click-listener to a button
 * 2. When clicked, the name is taken from the member search box
 * 3. The name is appended to the hidden input and appended to the list
 * 4. A button for removing the name is also created
 * 5. When the form is submitted, the api endpoint handles splitting the hidden input and creating new members
 *
 * Additional listeners are created to enable/disable the create and submit buttons.
 *
 * Note that a certain layout of the elements is assumed.
 */
const add_ajax_multiselect_extension = ({ selector_button, selector_input, selector_submit }) => {
	const create_member_button = $(selector_button);
	const submit_button = $(selector_submit);
	const input = $(selector_input);

	// Return if not all needed elements are found
	if (!create_member_button.length || !submit_button.length || !input.length) return;

	// Assume the hidden input and the deck comes directly after the normal input element
	const hidden_input = input.next();
	const deck = hidden_input.next();

	// Listen on input to enable/disable create button
	input.on("input", e => {
		const value = e.target.value;
		create_member_button.prop("disabled", !value || !value.trim().includes(" "));
	});

	const handleDisablingSubmit = () => submit_button.prop("disabled", deck.children().length == 0);

	// Listen for changes in the list of members to enable/disable submit button
	const observer = new MutationObserver(() => {
		input.trigger("input");
		handleDisablingSubmit();
	});
	observer.observe(deck.get(0), { childList: true });
	handleDisablingSubmit();

	// Handle creating new members
	create_member_button.click(e => {
		e.preventDefault();

		const name = input.val().trim();
		if (!name || !name.includes(" ") || name.includes("|") || name.includes("$")) return;
		input.val("");

		// Add name to hidden (real) input
		const substring = `$${name}|`;
		hidden_input.val(hidden_input.val() + substring);

		// Keep track of the amount of names added by storing the counter on the form
		const data = input.closest("form").data();
		data.counter = (data.counter || 0) + 1;

		// Add name to list
		const div = $("<div>", {
			html: `<b>Ny:</b> ${name}`,
		}).appendTo(deck);

		// Create button for removing the name from the list
		$("<span>", {
			class: "ui-icon ui-icon-trash",
			text: "X",
			click: () => {
				const value = hidden_input.val();
				const i = value.indexOf(substring);
				hidden_input.val(value.slice(0, i) + value.slice(i + substring.length));
				data.counter--;
				div.remove();
			},
		}).prependTo(div);
	});
}

const confirmMessageCreateMembers = e => {
	const newMembers = e.data("counter");
	return newMembers && `Du håller på att skapa ${newMembers === 1 ? "1 ny medlem" : `${newMembers} nya medlemmar`}. Fortsätt?`;
}

$(document).ready(function () {
	add_request_listener({
		selector: "#new-mgtftd-form",
		method: "POST",
		url: element => `/api/${element.data("active")}/`,
		newLocation: (element, msg) => `/admin/${element.data("active")}/${msg.id}/`,
	});

	add_request_listener({
		selector: "#choose-multiple-applicants-form",
		method: "POST",
		url: "/api/multi-applicantsubmissions/",
		newLocation: "/admin/applicants/",
	});	

	$('#side-search').keyup(function(event) {
		var active = $(this).data('active');
		var filter = $(this).val().toLowerCase();

		// If members, search with ajax_select Django app by doing a GET request
		if (active === 'members') {
			timer && clearTimeout(timer);
			timer = setTimeout(function(){
				$.ajax({
					// XXX: Why ')'???
					url: `/ajax_select/ajax_lookup/member)?term=${filter || "__ALL__"}`,
					method: "GET",
				}).done(function(data) {
					$("#side-objects").empty();
					$.each(data, function(i, item) {
						var a = '<a class="list-group-item" href="/admin/members/'+ item.pk +'/">'+ item.match +'</a>'
						$("#side-objects").append(a);
					});
				});
			}, 300);

		// If not members, simply hide/unhide the elements
		} else {
			const queries = filter.split(" ").filter(s => s);
			$("#side-objects a").each(function () {
				const element = $(this);
				let show = true;
				// All parts of the query need to match the content
				const text_content = element.text().toLowerCase();
				const search_attribute = element.attr("search").toLowerCase();
				for (const q of queries) {
					// Check both text and 'search' attribute
					if (!text_content.includes(q) && !search_attribute.includes(q)) {
						show = false;
						break;
					}
				}
				element.css("display", show ? "" : "none");
			});
		}
	});

	/**
	 * Populate "create new xyz" modal form with the current search box value.
	 */
	$("#side-new").click(() => {
		const search = $("#side-search");
		const value = search.val();
		switch (search.data("active")) {
			case "members": {
				const names = value.split(" ").filter(s => s).map(s => s[0].toUpperCase() + s.slice(1));
				if (names.length === 1) {
					return $("#mmodal_given_names").val(names.join(" "));
				}
				const last = names.splice(names.length - 1, 1);
				$("#mmodal_given_names").val(names.join(" "));
				$("#mmodal_surname").val(last);
			} break;
			case "decorations": $("#dmodal_name").val(value); break;
			case "grouptypes": $("#gtmodal_name").val(value); break;
			case "functionarytypes": $("#ftmodal_name").val(value); break;
		}
	});

	$('[data-toggle="tooltip"]').tooltip({
		placement : 'top'
	});

	/**
	 * Make elements function as clickable links.
	 */
	$(".clickable").click(function() {
		window.location = $(this).data("href");
	});

	/**
	 * Populate modal for editing a decoration ownership.
	 * Can not be placed in functionary.js because it is needed on the member page too.
	 */
	$(".edit-do-button").click(function() {
		const id = $(this).data("id");
		$("#edit-do-modal .modal-body").load(`/admin/decorationownerships/${id}/form/`, () => {
			add_request_listener({
				selector: "#edit-do-form",
				method: "PUT",
				url: `/api/decorationownerships/${id}/`,
			});

			$("#edit-do-modal").modal();
		});
	});

	/**
	 * Populate modal for editing a functionary.
	 * Can not be placed in decoration.js because it is needed on the member page too.
	 */
	$(".edit-f-button").click(function() {
		const id = $(this).data("id");
		$("#edit-f-modal .modal-body").load(`/admin/functionaries/${id}/form/`, () => {
			add_request_listener({
				selector: "#edit-f-form",
				method: "PUT",
				url: `/api/functionaries/${id}/`,
			});

			$("#edit-f-modal").modal();
		});
	});

	/**
	 * Set focus on the first (visible) input element in the form when opening any modal. All modals should have an id ending with '-modal'.
	 */
	$("[id$='-modal']").on("shown.bs.modal", function() {
		$(this).find("form :input:visible:first").focus();
	})

	/**
	 * Make it as easy as possible to set a date interval to be a full year. The default date interval is '1.1.YYYY' - '31.12.YYYY', where YYYY is the current year. The idea is that changing the year in the begin_date should automatically change the end_date year too, since one year intervals are by far the most common.
	 */
	$("[id$=form_begin_date]").change(function () {
		const begin_element = $(this);
		const begin_value = begin_element.val();

		// Continue only if the begin_date is (still) January 1
		if (!begin_value?.endsWith("-01-01")) return;

		// Find the end_date input element
		const end_id = begin_element.attr("id").replace("begin", "end");
		const end_element = $(`#${end_id}`);

		// Continue only if the end_date is (still) December 31
		if (!end_element.val()?.endsWith("-12-31")) return;

		// Set the end_date year equal to the begin_date year
		end_element.val(`${begin_value.split("-")[0]}-12-31`);
	});
});
