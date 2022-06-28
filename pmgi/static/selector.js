// Hard code the column indexes
let idi = 0;        // ID string
let nami = 1;       // name
let mwi = 2;        // molecular weight
let coli = 3;       // collection
let clsi = 4;       // class
// Use a global variable for the datatable object so it will be 
// available to all functions.
var sTable;
// Hard code the 


//**************
// Cookie management functions
//**************

// Set the cookie that remembers which idstring was selected
function set_idstr(idstr){
    // Set the cookie to expire in one hour
    exp = new Date();
    exp.setTime(exp.getTime() + 3600000);
    document.cookie= 'idstr=' + idstr + ';expires=' + exp;
}

// Retrieve the previously stored ID string value
function get_idstr(){
    let pairs = decodeURIComponent(document.cookie).split(';');
    let declare, param, value;
    // Loop over the parameter-value pairs
    for(declare of pairs){
        // Split by =
        pair = declare.split('=')
        if(pair.length == 2){
            param = pair[0].trim();
            value = pair[1].trim();
            if(param=='idstr'){
                return value;
            }
        }
    }
    return '';
}

// Clear the cookie
function del_idstr(){
    // Set the cookie to expire in the past
    document.cookie= 'idstr=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;'
}

function select(idstr){
    let selection = document.getElementById('selection');
    set_idstr(idstr);
    selection.innerHTML = get_idstr();
}


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
    rowi = 0
    for (idstr in substances){
        subst = substances[idstr];
        if (subst.nam.length>0){
            name = subst.nam[0];
        }else{
            name = '';
        }
        
        idtag = '<a class="clickable" href=javascript:select("' + idstr + '")>' + idstr + '</a>'
        
        // Add the row
        // ID, name, MW, collection, class
        sTable.row.add([idtag, name, subst.mw, subst.col, subst.cls]);
        rowi += 1;
    }
    
    // https://datatables.net/examples/plug-ins/range_filtering.html
    // Register the filter() function for selecting rows
    // This is JQuery obfuscation magic.
    $.fn.dataTable.ext.search.push(filter);
    
    // Adjust the column sizes to match the window
    sTable.columns.adjust().draw()
}

// The init() function is responsible for executing an AJAX call
// to the info interface to obtain the list of valid substances.  It
// registers the data_read() function for callback when the data are
// ready for writing to the table.
function init(){
    let message = document.getElementById('message');
    let selection = document.getElementById('selection');
    const rqst = new XMLHttpRequest();
    
    selection.innerHTML = get_idstr();
    message.innerHTML = 'Waiting for PMGI response...';

    // Request the data from the server
    rqst.onload = data_ready;
    rqst.open('GET', 'http://127.0.0.1:5000/info');
    rqst.send();
}


// Register the initialization function
window.onload = init;

