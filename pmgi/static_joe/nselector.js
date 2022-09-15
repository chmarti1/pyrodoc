// Hard code the column indexes
let idi = 0;        // ID string
let nami = 1;       // name
let mwi = 2;        // molecular weight
let coli = 3;       // collection
let clsi = 4;       // class
// Use a global variable for the datatable object so it will be
// available to all functions.
var sTable;


// SEL_UPDATE_FILTER
//      sel_update_filter()
// This is a wrapper function for sTable.draw(), which provides access
// to the global sTable object.  This is the callback function to update
// the selector table based on the filter.
function sel_update_filter(){
    sTable.draw();
}

// SEL_FILTER
//      sel_filter(settings, data, dataIndex)
// The filter function is used to apply the filter settings to each row
// It returns true when the row should be included.  The template for
// the filter function is specified by the DataTables interface.  The
// only argument used is data, which is an array of the row values, used
// to apply the filter.
//
// When SEL_FILTER returns true, the row will be included by the filter.
// When SEL_FILTER returns false, the row will be excluded by the
// filter.  The SEL_FILTER is applied as a callback to the DataTables in
// the SEL_DATA_READY function.
function sel_filter(settings, data, dataIndex){
    let mw = data[mwi];
    let col = data[coli];
    let cls = data[clsi];

    let mw_min = parseFloat(document.getElementById('filt_mw_min').value);
    let mw_max = parseFloat(document.getElementById('filt_mw_max').value);
    let col_ = document.getElementById('filt_col').value;
    let cls_ = document.getElementById('filt_cls').value;

    return (isNaN(mw_min) || mw >= mw_min) &&
        (isNaN(mw_max) || mw <= mw_max) &&
        (col_ == '' || col == col_) &&
        (cls_ == '' || cls == cls_);
}


function sel_select(idstr){
    let ok = confirm("Changing the substance will clear all data. Do you want to proceed?")
    if (ok){
        change_substance(idstr)
    } else {
        // ignore
    }
}

function sel_cancel(){
    onclick_changesubstance();
}

// SEL_DATA_READY
//      sel_data_ready()
// The SEL_DATA_READY function is the callback function for when the
// PMGI response comes back with the available substances.  It populates
// the rows of the selector table row-by-row.
//
// SEL_DATA_READY is assigned as a callback to the sTable object in the
// SEL_INIT function.
function sel_data_ready(data){
    let substances = data.substances;
    // Initialize the data table
    if (sTable === undefined) {
        sTable = new DataTable('#selector_table', {});
    }


    // Loop over each of the substances
    rowi = 0
    for (idstr in substances){
        subst = substances[idstr];
        // Parse the name
        if (subst.nam.length>0){
            name = subst.nam[0];
        }else{
            name = '';
        }

        idtag = '<a class="clickable" href=javascript:sel_select("' + idstr + '")>' + idstr + '</a>'

        // Add the row
        // ID, name, MW, collection, class
        sTable.row.add([idtag, name, subst.mw, subst.col, subst.cls]);
        rowi += 1;
    }

    // https://datatables.net/examples/plug-ins/range_filtering.html
    // Register the filter() function for selecting rows
    // This is JQuery obfuscation magic.
    $.fn.dataTable.ext.search.push(sel_filter);

    // Adjust the column sizes to match the window
    sTable.columns.adjust().draw()
}