class Subject {
    // https://webdevstudios.com/2019/02/19/observable-pattern-in-javascript/
    constructor() {
        this.listeners = [];
    }

    addListener(listener) {
        this.listeners.push(listener);
    }

    removeListener(listener) {
        const removeIndex = this.listeners.findIndex(obs => {
            return listener === obs;
        });

        if (removeIndex !== -1) {
            this.listeners = this.listeners.slice(removeIndex, 1);
        }
    }

    notify(subObj) {
        if (this.listeners.length > 0) {
            this.listeners.forEach(listener => listener(subObj));
        }
    }
}

class UnitConfig extends Subject{
    constructor() {
        super();
        this.units = {};
        this.valid_units = {};
    }

    update_units(units, valid_units=null){
        this.units = units;
        if (valid_units !== null){
            this.valid_units = valid_units;
        }
        this.notify(this)
    }
}

var unitMaster;

// Execute when the page loads
$(document).ready(function(){
    unitMaster = new UnitConfig();
    unitMaster.addListener(setup_units);
    get_info();
});

function setup_units(unitConfig){
    // Get the unit JSON from the data
    let units = unitConfig.units;
    let valid_units = unitConfig.valid_units;

    // Loop over all the configured unit types
    Object.keys(valid_units).forEach(val => {
        // The form will be a list of labelled select boxes
        let $li = $("<li>")
        let $label = $('<label>'+val.charAt(0).toUpperCase() + val.slice(1)+'</label>', {});
        let $select = $('<select/>', {'name': val});

        // Loop over each valid unit within the given unit category
        valid_units[val].forEach(opt => {
            // Add an option to the select that corresponds to it
            $select.append($("<option>").val(opt).text(opt));
        });
        // Set the selected value
        $select.val(units[val]);
        // Add the objects to the form
        $('#unitform').append($li.append($label).append($select));
    });
    unitMaster.removeListener(setup_units);
}


function get_info(){
    $.get("/info", function (data){
        unitMaster.update_units(data.units, data.valid_units);
    },
    dataType='json')
    .fail(propResponseFail);
}


function popup() {
    // TODO - make this a units edit place
   var popwindow = document.getElementById("checkBundle");
   if (popwindow.style.display === "none") {
       popwindow.style.display = "block";
  } else {
        popwindow.style.display = "none";
    }
}

/**
 * Convert the properties form object into JSON that is suitable for passing to
 * PMGI.
 *
 * Form elements must have a "name" field. The keys of the JSON will be
 * shortened using only the first letter of the name. In order to be useful
 * with PMGI, the form element names should all use their PMGI property
 * identifier as their first letter.
 *
 * @param formID the Element ID of the form
 * @returns Object, keyed by thermodynamic property, with values as floats.
 */
function propFormToJSON(formID, append){

    let outdata = {};
    let data = Object.fromEntries(new FormData(document.getElementById(formID)));
    for (const key in data) {
        let shortkey = key[0];
        let v = parseFloat(data[key]);
        if (v){
            outdata[shortkey] = v;
        }
    };

    if (append !== undefined){
        for (const key in append){
            outdata[key] = append[key];
        }
    }
    return outdata;
}


function buildTable(data){
    var table = document.getElementById("proptable");
    var row = table.insertRow(table.rows.length-1);
    row.insertCell(0).innerHTML = data.T;
    row.insertCell(1).innerHTML = data.p;
    row.insertCell(2).innerHTML = data.d;
    row.insertCell(3).innerHTML = data.h;
    row.insertCell(4).innerHTML = data.s;
}



function propResponseSuccess(data){
    // TODO generalize!!
    buildTable(data.data);
}

function propResponseFail(data){
    // TODO better error handling?
    try {
       let resp = JSON.parse(data.responseText);
       alert(resp.message);
    } catch (error) {
       alert("An unhandled error occurred: " + data.responseText);
    }
}


function postProps(){
    let requestroute = "/";
    let formData = propFormToJSON('propform', {'id': 'mp.H2O'});
    let unitFormData = Object.fromEntries(new FormData(document.getElementById("unitform")));
    let postData = {state_input: formData, units: unitFormData};
    // Forced to operate as $.ajax because we need to specify that we're
    // passing json.
    $.ajax({
        url: requestroute,
        type: "POST",
        data: JSON.stringify(postData),
        dataType: "json",
        contentType: 'application/json; charset=utf-8',
        success: propResponseSuccess,
        error: propResponseFail
    });
}


function getProps(){
    let requestroute = "/";
    let formData = propFormToJSON('propform', {'id': 'mp.H2O'});
   $.get(requestroute, formData, propResponseSuccess,dataType='json')
    .fail(propResponseFail);
}


// Based on an example from stackoverflow
function populate_list() {
    $.getJSON("/Admin/GetFolderList/", function(result) {
        var $dropdown = $("#dropdown");
        $.each(result, function() {
            $dropdown.append($("<option />").val(this.ImageFolderID).text(this.Name));
        });
    });
}

//
// function updateinputs() {
//     // First, count the number of nonzero entries
//     var count;
//     var inputs = [document.getElementById("Tinput"), document.getElementById("pinput"), document.getElementById("dinput"), document.getElementById("hinput"), document.getElementById("sinput")];
//     var x;
//
//     count = 0;
//     for (x of inputs){
//         if (x.value.length){
//             count += 1;
//         }
//     }
//
//     if(count < 2){
//         for (x of inputs){
//             x.disabled = false;
//         }
//     }else{
//         for (x of inputs){
//             if (x.value.length==0){
//                 x.disabled = true;
//             }
//         }
//     }
//
//     // Then, grey out the entries that are zero (if appropriate)
// }
