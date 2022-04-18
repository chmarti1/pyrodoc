// *********************************************
// * PAGE CREATION OUTLINE
// *********************************************
// * * Create HTML Document
// * * Get Info from Pyromat
// * * * Create Units selector
// * * * Create substance selector
// * * Define Current Units
// * * Define Current Substance
// * * Initialize User-specified Data Model
// * * Initialize Plot
// * * * Compute steam dome/isolines
// * * * Initialize Point Trace
// * * * Create Plot Axis Selector
// * * Initialize Table
// * * Allow User Interaction
// * * * Create Points
// * * * Delete Points
// * * * Change Units
// * * * Change Substance
// * * * Change display options?


// *********************************************
// * CLASSES
// *********************************************

// A parent class for a observables that notify listeners when they get changed
// In this case, listener is just a function object that will be called.
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

// An instance of observable that will hold the current unit configuration and
// notify when it is changed
class UnitConfigSubject extends Subject{
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

    cfgAsJSON(){
        return Object.fromEntries(new FormData(document.getElementById("unitform")));
    }
}

// An instance of observable that will hold an array of individual thermodynamic
// points that have been computed.
class PointSubject extends Subject{
    constructor() {
        super();
        this.points = undefined
    }

    add_point(point){
        if (this.points === undefined){
            this.points = {};
            for (const key in point) {
                this.points[key] = [point[key]];
            }
        } else {
            for (const key in point) {
                this.points[key].push(point[key]);
            }
        }
        this.notify(this.points)
    }
}


class Plot{
    constructor(targetDiv) {
        this.x_prop = 's';
        this.y_prop = 'T';
        this.container = targetDiv;
        this.layout();
      let traces = [{
          x: [],
          y: [],
          mode: 'markers',
          type: 'scatter'
      }];
        //data.push({x:0,y:0})
        Plotly.newPlot(this.container, traces, this.layout);
    }

    layout(){
        let x_scale;
        let y_scale;
        if (this.x_prop == 'v'){
            x_scale = 'log';
        } else {
            x_scale = 'linear';
            }
        if (this.y_prop == 'p'){
            y_scale = 'log';
        } else {
            y_scale = 'linear';
        }

        this.layout = {
            xaxis: {
                type: x_scale,
                autorange: true
            },
            yaxis: {
                type: y_scale,
                autorange: true
            },
            margin: { t: 0 }
        };

    }
    updatePoints(point) {
        let data = {
            x: [[point[this.x_prop]]],
            y: [[point[this.y_prop]]]
        }
        Plotly.extendTraces(this.container, data, [0]);
    }
}


// *********************************************
// * PAGE SETUP
// *********************************************

// Instantiate the classes
var unitMaster;
var pointMaster;
var plotMaster;


// Execute when the page loads
$(document).ready(function(){
    unitMaster = new UnitConfigSubject();
    unitMaster.addListener(setup_units);

    pointMaster = new PointSubject();
    pointMaster.addListener(buildTable);
    pointMaster.addListener(drawPlot);

    plotMaster = new Plot(document.getElementById("plot"));

    // This function extracts info from Pyromat
    getInfo();
});


function setup_units(unitConfig){
    //Program flow is -
    // - Setup document
    // - this function listens for when units are ready
    // - get unit info from pyromat
    // - get notified -> set up the form

    // Get the unit JSON from the data
    let units = unitConfig.units;
    let valid_units = unitConfig.valid_units;

    // Loop over all the configured unit types
    Object.keys(valid_units).forEach(unit_cat => {
        // The form will be a list of labelled select boxes
        let $li = $("<li>")
        let capital_name = unit_cat.charAt(0).toUpperCase() + unit_cat.slice(1);
        let $label = $('<label>'+capital_name+'</label>', {});
        let $select = $('<select/>', {'name': unit_cat});

        // Loop over each valid unit within the given unit category
        valid_units[unit_cat].forEach(unit_opt => {
            // Add an option to the select that corresponds to it
            $select.append($("<option>").val(unit_opt).text(unit_opt));
        });
        // Set the selected value
        $select.val(units[unit_cat]);
        // Add the objects to the form
        $('#unitform').append($li.append($label).append($select));
    });
    unitMaster.removeListener(setup_units);
}

// *********************************************
// * DATA DISPLAY
// *********************************************


function buildTable(data){
    // Respond to additional points being added
    let table = document.getElementById("proptable");
    let lasti = data['T'].length-1;
    let row = table.insertRow(table.rows.length-1);
    row.insertCell(0).innerHTML = data["T"][lasti];
    row.insertCell(1).innerHTML = data["p"][lasti];
    row.insertCell(2).innerHTML = data["d"][lasti];
    row.insertCell(3).innerHTML = data["h"][lasti];
    row.insertCell(4).innerHTML = data["s"][lasti];
}

function drawPlot(data){
    let lasti = data['T'].length-1;
    let point = {};
    for (const key in data) {
        point[key] = data[key][lasti];
    }
    plotMaster.updatePoints(point);
}


// *********************************************
// * INTERACTIVITY
// *********************************************

function popup() {
    // TODO - make this a units edit place
   var popwindow = document.getElementById("hideablelist");
   if (popwindow.style.display === "none") {
       popwindow.style.display = "block";
  } else {
        popwindow.style.display = "none";
    }
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


// *********************************************
// * COMMUNICATION WITH SERVER
// *********************************************




function propResponseSuccess(data){
    // TODO generalize!!
    pointMaster.add_point(data.data);
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
    let unitFormData = unitMaster.cfgAsJSON();
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


function getInfo(){
    // Get all the PM info.
    // TODO - the list of substances
    $.get("/info", function (data){
        unitMaster.update_units(data.units, data.valid_units);
    },
    dataType='json')
    .fail(propResponseFail);
}



/**
 * Convert the properties form's data into JSON that is suitable for passing to
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
    //TODO - probably make this more general
    let outdata = {};
    let data = Object.fromEntries(new FormData(document.getElementById(formID)));
    for (const key in data) {
        // The key we need for the JSON is just a single letter, not the full name
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


