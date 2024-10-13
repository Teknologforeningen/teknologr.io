/**
 * Order the rows of a table according to a specific column.
 */
const sortTable = ({ tbody, column, reverse, from_attribute }) => {
    const selector = `td:eq(${column})`;

    // The data to order can be gotten from either the cell text itself or from the 'order-data' attribute, since ordering by the text is not always suitable. For example names might want to be ordered by surname but displayed as "<first_names> <surname>", and dates might be displayed in a certain format but must (and can) be compared using the YYYY-MM-DD format.
    let getData;
    if (from_attribute) {
        getData = a => $(selector, a).attr("order-data") || "";
    } else {
        getData = a => $(selector, a).text();
    }

    // localeCompare() can compare numbers as strings when the 'numeric' option is set.
    // XXX: The locale is hardcoded to 'sv' here, but it should probably be handled in some other way
    const compareFn = (a, b) => getData(b).localeCompare(getData(a), "sv", { usage: "sort", sensitivity: "base", numeric: true });

    let rows = tbody.find("tr");
    if (reverse) {
        rows = rows.sort((a, b) => compareFn(a, b));
    } else {
        rows = rows.sort((a, b) => compareFn(b, a));
    }
    rows.appendTo(tbody);
}

/**
 * Apply the correct sorting icon to a column header, and automatically reset the previous icon. Also store the icon, if active, so that it can be used to deduce the currently ordered column later.
 *
 * This needs to take into account that there can be several tables/tbodys on same page, each with their own active column/icon, so therefore the active icon is stored in the tbody.
 */
const handleIcon = (tbody, icon, active, reversed) => {
    icon.removeClass();
    icon.addClass("fa fa-2xs");

    if (!active) return icon.addClass("fa-sort");

    // Reset the previously active icon if there is one
    const activeIcon = getActiveIcon(tbody);
    if (activeIcon && activeIcon !== icon) handleIcon(tbody, activeIcon);

    icon.addClass(reversed ? "fa-sort-down reversed" : "fa-sort-up");
    setActiveIcon(tbody, icon);
}
const setActiveIcon = (tbody, icon) => $(tbody).data("active-icon", icon);
const getActiveIcon = (tbody) => $(tbody).data("active-icon");


$(document).ready(() => {
    /**
     * Setup tables to be sortable by listening for clicks on columns with the 'order-by' class. If only the header text should be clickable the class can be added to a <span> element instead of to the <th> element.
     *
     * The order is reversed if the same column is clicked twice in a row. Also, the order is preserved between columns, meaning that reversing the order on one column means that the first click on any other column will also result in a reversed order.
     *
     * Icons are also added beside each header that are sortable, and changes depending on which column is sorted.
     *
     * The initial order can be given by using the 'default-order' or 'default-order-reversed' class on the header in question.
     *
     * The data location and method of comparison can be changed by adding the classes 'attributes' and 'dates'.
     */
    $(".order-by").each((_, e) => {
        const tbody = $(e).closest("thead").next("tbody");
        if (!tbody) return;

        // Get info for sorting
        const column = $(e).closest("th").index().toString();
        const from_attribute = $(e).hasClass("attribute");

        // Create an icon for this header
        const icon = $("<i></i>");
        icon.css("padding-left", "4px");
        const b = $(e).hasClass("default-order-reversed");
        handleIcon(tbody, icon, b || $(e).hasClass("default-order"), b);
        $(e).append(icon);

        e.onclick = () => {
            // Let's use the icons to also figure out the currently sorted column and order
            const activeIcon = getActiveIcon(tbody);
            let reverse = activeIcon?.hasClass("reversed");
            if (activeIcon === icon) reverse = !reverse;

            sortTable({
                tbody,
                column,
                reverse,
                from_attribute,
            });

            // Set the icon for this header (which will also reset the icon for hte previous header)
            handleIcon(tbody, icon, true, reverse);
        }
    });

    /**
     * Make the searchbox into a filter too, filtering all table rows on the page.
     */
    $("#searchboxfilter").on("input", event => {
        const queries = event.target.value.toLowerCase().split(" ").filter(s => s);
        $("tbody tr").each((_, e) => {
            const str = e.children[0].textContent.toLowerCase();
            let ok = true;
            for (const q of queries) {
                if (!str.includes(q)) {
                    ok = false;
                    break;
                }
            }
            e.style.display = ok ? "" : "none";
        });
    });
});
