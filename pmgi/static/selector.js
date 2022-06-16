// Hard code the column indexes
let idi = 0;
let nami = 1;
let mwi = 2;
let coli = 3;
let clsi = 4;
var sTable;

function update_filter(){
    sTable.draw();
}

// The filter function is used to apply the filter settings to each row
// It returns true when the row should be included.
function filter(settings, data, dataIndex){
    let mw = data[mwi];
    let col = data[coli];
    let cls = data[clsi];
    
    let mw_min = parseFloat(document.getElementById('mw_min').value);
    let mw_max = parseFloat(document.getElementById('mw_max').value);
    let col_ = document.getElementById('collection').value;
    let cls_ = document.getElementById('class').value;
    
    return (isNaN(mw_min) || mw >= mw_min) && 
        (isNaN(mw_max) || mw <= mw_max) &&
        (col_ == '' || col == col_) &&
        (cls_ == '' || cls == cls_);
}

// This callback function will be called when the PGMI interface returns
// the list of substances.  It is used to build the table.
function data_ready(){
    // Parse the response and break it into its parts
    let response = JSON.parse(this.responseText);
    let data = response.data;
    let substances = data.substances;
    let message = response.message;
    let args = response.args;
    let units = response.units;
    // Initialize the data table
    sTable = new DataTable('#selector_table', {});
    
    // Deal with any error messages
    let mesdiv = document.getElementById('message');
    mesdiv.innerHTML = message.message;
    

    
    // Loop over each of the substances
    for (idstr in substances){
        subst = substances[idstr];
        if (subst.nam.length>0){
            name = subst.nam[0];
        }else{
            name = '';
        }
        
        // Add the row
        // ID, name, MW, collection, class
        sTable.row.add([idstr, name, subst.mw, subst.col, subst.cls]);
    }
    
    // https://datatables.net/examples/plug-ins/range_filtering.html
    // Register the filter() function for selecting rows
    $.fn.dataTable.ext.search.push(filter);
    
    sTable.columns.adjust().draw()
}

// The st_init() function is responsible for executing an AJAX call
// to the info interface to obtain the list of valid substances.  It
// registers the data_read() function for callback when the data are
// ready for writing to the table.
function init(){
    let message = document.getElementById('message');
    const rqst = new XMLHttpRequest();
    
    message.innerHTML = 'Init ran.';

    // Request the data from the server
    rqst.onload = data_ready;
    rqst.open('GET', 'http://127.0.0.1:5000/info');
    rqst.send();
}


// Register the initialization function
window.onload = init;

