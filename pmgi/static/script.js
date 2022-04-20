// *********************************************
// * PAGE CREATION OUTLINE
// *********************************************
// * * Create HTML Document
// * * Get Info from Pyromat
// * * * Create Units selector +
// * * * Create substance selector +
// * * Define Current Units +
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
Number.prototype.between = function(min, max) {
  return this >= min && this <= max;
};


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
class InfoSubject extends Subject{

    SUB_SHORTLIST=["H2O","C2H4F4","air","O2", "N2"];;

    constructor() {
        super();
        this.units = {};
        this.valid_units = {};
        this.substances = {};
    }

    set_data(units, valid_units=null, substances=null){
        if (valid_units !== null){
            this.valid_units = valid_units;
        }
        if (substances !== null){
            this.substances = substances;
        }
        this.change_units(units)
    }

    change_units(units){
        this.units = units;
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
        this.points = []
    }

    recalculate(){
        // Pass points back to Python
    }

    add_point(point){
        if (this.points.length === 0){
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

    delete_point(id){
        for (const key in this.points) {
            this.points[key].splice(id, 1);
        }
        this.notify(this.points);
    }

    clearpoints(){
        this.points = [];
        this.notify(this.points);
    }
}


class Plot{
    constructor(targetDiv) {
        this.x_prop = 's';
        this.y_prop = 'T';
        this.dispprops = ['T','s','p','v'];
        this.container = targetDiv;
        this.updatePoints = this.updatePoints.bind(this);
        this.layout();
        let traces = [{
            x: [],
            y: [],
            customdata: [1],
            mode: 'markers',
            hovertemplate: "<b> Point prop<br>"+
                this.x_prop+": %{x}<br>" +
                this.y_prop+": %{y}<br>" +
                "attr: %{customdata: .2f}",
            type: 'scatter'
        }];
        //data.push({x:0,y:0})
        Plotly.newPlot(this.container, traces, this.layout);
        this.setupclicklistener();
    }

    setupclicklistener(){
        let myPlot = this.container;
        let myPlotContainer = this;
        d3.select(".plotly").on('click', function(d, i) {
          var e = d3.event;
          var bgrect = document.getElementsByClassName('gridlayer')[0].getBoundingClientRect();
            var x = ((e.x - bgrect['x']) / (bgrect['width'])) * (myPlot.layout.xaxis.range[1] - myPlot.layout.xaxis.range[0]) + myPlot.layout.xaxis.range[0];
            var y = ((e.y - bgrect['y']) / (bgrect['height'])) * (myPlot.layout.yaxis.range[0] - myPlot.layout.yaxis.range[1]) + myPlot.layout.yaxis.range[1];
          if (x.between(myPlot.layout.xaxis.range[0], myPlot.layout.xaxis.range[1]) &&
            y.between(myPlot.layout.yaxis.range[0], myPlot.layout.yaxis.range[1])) {
              let formData = {}
              formData['id'] = 'mp.H2O';
              formData[myPlotContainer.x_prop] = x
              formData[myPlotContainer.y_prop] = y
                  let requestroute = "/";
              let unitFormData = infoContainer.cfgAsJSON();
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
        });
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

    updatePoints(points) {
        // Build the customdata object for the tooltip
        // Object has the form [[h1,v1,s1],[h2,v2,s2],[h3,v3,s3]]

        let allkeys = Object.keys(points);
        let customdataset = [];  // The custom data that will be added to the tooltip
        let keylist = [];
        for (let i=0; i<points['T'].length; i++ ){  // Loop over all points
            let arr = [] // Build an array of all props for this index.
            arr.push(i); // Make the index the very first datapoint.

            allkeys.forEach(key => {
                if (key !== this.x_prop &&
                    key !== this.y_prop &&
                    this.dispprops.includes(key)) {
                    if (i==0) {
                        keylist.push(key);
                    }
                    arr.push(points[key][i]);
                }
            });
            customdataset.push(arr);
        }

        // customdataset is now (id, <insert keylist>)

        // Build the strings that identify the points
        let customrows = "";
        for (let i=0; i<keylist.length; i++){
            customrows = customrows + keylist[i] + ": %{customdata["+(i+1)+"]}<br>";
        }

        // Fully replace trace, including the custom data
        let update = {
            x: [points[this.x_prop]],
            y: [points[this.y_prop]],
            customdata: [customdataset],
            hovertemplate: "<b> Point %{customdata[0]}<br>"+
                this.x_prop+": %{x}<br>" +
                this.y_prop+": %{y}<br>" +
                customrows,
        }
        Plotly.restyle(this.container, update, [0]) // May need to adjust traceID to accommodate the isolines, etc.
    }
}

class Table{
    // delete rows? https://stackoverflow.com/questions/64526856/how-to-add-edit-delete-buttons-in-each-row-of-datatable
    constructor(targetDiv) {
        this.dispprops = ['T','p','d','h','s'];
        this.container = targetDiv;
        this.updatePoints = this.updatePoints.bind(this);
        let table = new DataTable('#proptable', {
            "columnDefs": [ {
                "targets": -1,
                "data": null,
                "defaultContent": "<button id='click2del'>Delete</button>"
            } ]
        });

        $(targetDiv + ' tbody').on( 'click', 'button', function () {
            var data = table.row( $(this).parents('tr') ).data();
            pointContainer.delete_point(data[0]);
        } );
        this.table = table;
    }

    updatePoints(points) {
        this.table.rows().remove();

        let customdataset = [];  // The custom data that will be added to the tooltip
        for (let i=0; i<points['T'].length; i++ ){  // Loop over all points
            let arr = [] // Build an array of all props for this index.
            arr.push(i);
            this.dispprops.forEach(key => {
                arr.push(points[key][i]);
            });
            customdataset.push(arr)
        }

        for (let i=0; i<customdataset.length; i++ ) {  // Loop over all rows
            this.table.row.add(customdataset[i]).draw();
        }
    }
}


function deletePoint(btn){
    alert("LOL");
}

// *********************************************
// * PAGE SETUP
// *********************************************

// Instantiate the classes
var infoContainer;
var pointContainer;
var plotContainer;
var tableContainer;


// Execute when the page loads
$(document).ready(function(){
    tableContainer = new Table('#proptable');

    plotContainer = new Plot(document.getElementById("plot"));

    // Listen for the Info callback from PMGI and update data
    infoContainer = new InfoSubject();
    infoContainer.addListener(setup_selects);
    getInfo();

    pointContainer = new PointSubject();
    pointContainer.addListener(plotContainer.updatePoints);
    pointContainer.addListener(tableContainer.updatePoints);


});


function setup_selects(data_subject, show_all=false){
    //Program flow is -
    // - Setup document
    // - this function listens for when units are ready
    // - get unit info from pyromat (getInfo())
    // - Update the Observable with the PMGI info data
    // - this gets notified -> set up the form

    // Remove from the list
    infoContainer.removeListener(setup_selects);

    // Get the unit JSON from the data
    let units = data_subject.units;
    let valid_units = data_subject.valid_units;
    let substances = data_subject.substances

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

    let subsel = $('#sel_substance');
    // Loop over the substances, create option group for each category
    Object.keys(substances).forEach(subgrp => {
        let optgroup = $('<optgroup>');
        optgroup.attr('label',subgrp);
        substances[subgrp].forEach(substance => {
            if (show_all || infoContainer.SUB_SHORTLIST.includes(substance)) {
                optgroup.append($("<option>").val(subgrp+"."+substance).text(substance));
            }
        });
        subsel.append(optgroup);
    });
    subsel.val('mp.H2O')

    infoContainer.addListener(onUnitsChanged);
}

// *********************************************
// * DATA DISPLAY
// *********************************************

function onUnitsChanged(infoMaster){
    // TODO - Handle behavior when units change
}


// function buildTable(data){
//     // Respond to additional points being added
//     // let table = document.getElementById("proptable");
//     // let lasti = data['T'].length-1;
//     // let row = table.insertRow(table.rows.length-1);
//     // row.insertCell(0).innerHTML = data["T"][lasti];
//     // row.insertCell(1).innerHTML = data["p"][lasti];
//     // row.insertCell(2).innerHTML = data["d"][lasti];
//     // row.insertCell(3).innerHTML = data["h"][lasti];
//     // row.insertCell(4).innerHTML = data["s"][lasti];
// }
//
// function drawPlot(data){
//     let lasti = data['T'].length-1;
//     let point = {};
//     for (const key in data) {
//         point[key] = data[key][lasti];
//     }
//     plotContainer.updatePoints(point);
// }


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


// Callbacks
function propResponseSuccess(data){
    // TODO generalize!!
    pointContainer.add_point(data.data);
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

// AJAX
function postProps(){
    let requestroute = "/";
    let formData = propFormToJSON('propform', {'id': 'mp.H2O'});
    let unitFormData = infoContainer.cfgAsJSON();
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
    $.get("/info", data=> {
            infoContainer.set_data(data.units, data.valid_units, data.substances);
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


