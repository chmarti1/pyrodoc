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

// Set a cookie value
//      set_cookie(param,value)
// This assigns a value to the string parameter name, param.  The cookie
// expiration is not set.
function set_cookie(param, value){
    // Set the cookie to expire in one hour
    set_cookie_exp(param,value,3600000);
}

// Set a cookie with an expiration value
//      set_cookie_exp(param,value,exp)
// This assigns a value to the string parameter name, param.  The cookie
// expiration is set to exp milliseconds from now.  To delete a cookie,
// pass a negative value to exp
function set_cookie_exp(param, value, exp){
    // Set the cookie to expire in one hour
    time = new Date();
    time.setTime(time.getTime() + exp);
    document.cookie= param + '=' + value + ';expires=' + time + ';path=/';
}

// GET_COOKIE
//      get_cookie(param)
// Recovers the value associated with a cookie with the string name, 
// param.  If no cookie with a matching param name is found, an empty
// string is returned.
function get_cookie(param){
    let pairs = decodeURIComponent(document.cookie).split(';');
    let tparam, declare, value;
    // Loop over the parameter-value pairs
    for(declare of pairs){
        // Split by =
        pair = declare.split('=')
        if(pair.length == 2){
            tparam = pair[0].trim();
            value = pair[1].trim();
            if(tparam==param){
                return value;
            }
        }
    }
    return '';
}

function goto_selector(from){
    set_cookie('from', from);
    window.location.href = '/selector';
}



//**********
// sel_XXX
//
//  These functions are for the selector page
//**********

// SEL_SELECT
//      sel_select(idstr)
// This function is called by clicking a substance selection link.  It
// calls set_idstr() to set the idstr cookie before returning to the 
// calling page.
function sel_select(idstr){
    let from = get_cookie('from');
    set_cookie_exp('from','',-1);
    set_cookie('idstr',idstr);
    document.getElementById('selection_id').innerHTML = get_cookie('idstr');
    if (from.length > 0){
        window.location = from;
    }
}


function sel_cancel(){
    let from = get_cookie('from');
    set_cookie_exp('from','',-1);
    if (from.length > 0){
        window.location = from;
    }
}

function sel_clear(){
    set_cookie_exp('idstr', '', -1);
    document.getElementById('selection_id').innerHTML = get_cookie('idstr');
}

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

// SEL_DATA_READY
//      sel_data_ready()
// The SEL_DATA_READY function is the callback function for when the 
// PMGI response comes back with the available substances.  It populates
// the rows of the selector table row-by-row.
//
// SEL_DATA_READY is assigned as a callback to the sTable object in the
// SEL_INIT function.
function sel_data_ready(){
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

// This is a general purpose function that navigates to the selection 
// after setting the "from" cookie.  From is used to navigate back to
// the source page after having selected a substance.
function selection_go(from){
    set_cookie('from',from);
    window.location = '/selector';
}


// SEL_INIT
//      sel_init()
// The sel_init() function is responsible for executing an AJAX call
// to the info interface to obtain the list of valid substances.  It
// registers the sel_data_read() function for callback when the data are
// ready for writing to the table.
function sel_init(){
    let from = get_cookie('from');
    let message = document.getElementById('message');
    const rqst = new XMLHttpRequest();
    
    document.getElementById('selection_id').innerHTML = get_cookie('idstr');
    if (from.length==0){
        document.getElementById('selection_cancel').disabled = true;
    }

    message.innerHTML = 'Waiting for PMGI response...';

    // Request the data from the server
    rqst.onload = sel_data_ready;
    rqst.open('GET', 'http://127.0.0.1:5000/info');
    rqst.send();
}


//**********
// SUBST_XXX
// Substance page functions
//**********

function subst_data_ready(){
    // Parse the response and break it into its parts
    let response = JSON.parse(this.responseText);
    let data = response.data;
    let substances = data.substances;
    let message = response.message;
    let args = response.args;
    let units = response.units;
    let formula = '';
    let qty = 0;
    let name, names='';
    let critical='', triple='';
    
    document.getElementById('message').innerHTML = message.message;
    
    document.getElementById('subst_id').innerHTML = data['id'];
    document.getElementById('subst_col').innerHTML = data['col'];
    document.getElementById('subst_cls').innerHTML = data['cls'];
    document.getElementById('subst_mw').innerHTML = data['mw'] + ' ' + units['mass'] + '/' + units['molar'];
    document.getElementById('subst_inchi').innerHTML = data['inchi'];
    document.getElementById('subst_cas').innerHTML = data['casid'];

    for (atom in data['atoms']){
        qty = data['atoms'][atom];
        if (qty == 1){
            formula += atom;
        }else{
            formula += atom + '<sub>' + qty + '</sub>';
        }
    }
    document.getElementById('subst_form').innerHTML = formula;
    
    for (name of data['names']){
        names += name + '<br>'
    }
    document.getElementById('subst_names').innerHTML = names;
    document.getElementById('subst_doc').innerHTML = data['doc'];
    
    if (data['Tc'] != undefined){
        critical += data['Tc'] + ' ' + units['temperature'] + '<br>'
    }
    if (data['pc'] != undefined){
        critical += data['pc'] + ' ' + units['pressure'] + '<br>'
    }
    if (data['dc'] != undefined){
        critical += data['dc'] + ' ' + units['matter'] + '/' + units['volume'] + '<br>'
    }
    document.getElementById('subst_crit').innerHTML = critical;
    
    if (data['Tt'] != undefined){
        triple += data['Tt'] + ' ' + units['temperature'] + '<br>'
    }
    if (data['pt'] != undefined){
        triple += data['pt'] + ' ' + units['pressure'] + '<br>'
    }
    document.getElementById('subst_triple').innerHTML = triple;
}

function subst_init(){
    let message = document.getElementById('message');
    let selection = document.getElementById('selection_id');
    const rqst = new XMLHttpRequest();
    let idstr = get_cookie('idstr');
    selection.innerHTML = idstr;
    message.innerHTML = 'Waiting for PMGI response...';

    // Request the data from the server
    rqst.onload = subst_data_ready;
    rqst.open('GET', 'http://127.0.0.1:5000/subst?id=' + encodeURIComponent(idstr));
    rqst.send();
}
