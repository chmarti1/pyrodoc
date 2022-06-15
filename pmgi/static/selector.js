

function data_ready(){
    // Parse the response and break it into its parts
    let response = JSON.parse(this.responseText);
    let data = response.data;
    let substances = data.substances;
    let message = response.message;
    let args = response.args;
    let units = response.units;
    // Initialize the data table
    let table = new DataTable('#selector_table', 
        {data:data});
    
    // Deal with any error messages
    let mesdiv = document.getElementById('message');
    mesdiv.innerHTML = message.message;
    
    // Loop over each of the substances
    for (idstr in substances){
        if (substances[idstr]['nam'].length>0){
            name = substances[idstr]['nam'][0];
        }else{
            name = '';
        }
        table.row.add([idstr, name, substances[idstr].mw]);
    }
    table.draw()
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

