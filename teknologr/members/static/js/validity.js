/* Some browsers (e.g. desktop Safari) does not have built-in datepickers (e.g. Firefox).
 * Thus we check first if the browser supports this, in case not we inject jQuery UI into the DOM.
 * This enables a jQuery datepicker.
 */

// add_request_listener({
//     selector: ".test",
//     method: "GET",
//     url: element => `/admin/validity/${element.data("target").slice(1)}/`,
//     // confirmMessage: "Vill du radera denna ansökan?",
//     // newLocation: "/admin/applicants/",
// });

$("#test-all").click(function () {
    $(".test").click();
});

$(".test").click(function () {
    const button = $(this);
    const target = button.prop("id");
    if (!target) return;

    button.prop("disabled", true);
    const icon = $(`#${target}-icon`);
    icon.show();

    const request = $.ajax({
        method: "GET",
        url: `/admin/validity/${target}/`,
    });

    const fail = () => {
        icon.attr("class", "fa fa-times-circle");
    }

    // Add listeners to the request
    request.done(msg => {
        const results = msg.results;
        if (!Array.isArray(results)) return fail();

        if (results.length === 0) return icon.attr("class", "fa fa-check-circle");

        icon.attr("class", "");
        icon.text(results.length);
        const div = $(`#${target}-results`);
        for (const r of results) {
            div.append(`<a href="${r.href}">&nbsp;&nbsp;${r.text}<a/><br/>`);
        }
        // div.show();
    });

    request.fail(fail);
});
