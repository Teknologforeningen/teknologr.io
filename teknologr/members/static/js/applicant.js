/* Some browsers (e.g. desktop Safari) does not have built-in datepickers (e.g. Firefox).
 * Thus we check first if the browser supports this, in case not we inject jQuery UI into the DOM.
 * This enables a jQuery datepicker.
 */

var datefield = document.createElement('input');
datefield.setAttribute('type', 'date');

if (datefield.type != 'date') {
    const jQueryUIurl = 'http://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1';
    document.write(`<link href="${jQueryUIurl}/themes/base/jquery-ui.css" rel="stylesheet" type="text/css" />\n`)
    document.write(`<script src="${jQueryUIurl}/jquery-ui.min.js"><\/script>\n`)
}

function setProgrammeChoice() {
    const programmeOptionsSelector = $('#id_degree_programme_options option');
    const programmeOptions = Object.values(programmeOptionsSelector).map(option => option.value);

    const currentProgramme = $('#id_degree_programme').val();
    if (programmeOptions.indexOf(currentProgramme) !== -1) {
        $('#id_degree_programme_options').val(currentProgramme);
    } else {
        $('#id_degree_programme_options').val('extra');
        $('#unknown_degree').show();
    }
}

$(document).ready(function() {

    // Set degree choice based on pre-existing data
    setProgrammeChoice();

    $('#id_degree_programme_options').change(function() {
        if (this.value === 'extra') {
            $('#unknown_degree').show();
            $('#id_degree_programme').val('');
        } else {
            $('#unknown_degree').hide();
            $('#id_degree_programme').val(this.value);
        }
    });

    // Set the datepicker on birth date, in case input type of date is not supported
    if (datefield.type != 'date') {
        const currentYear = new Date().getFullYear();

        $('#id_birth_date').datepicker({
            changeMonth: true,
            changeYear: true,
            yearRange: `1930:${currentYear}`,
        });
    }
});
