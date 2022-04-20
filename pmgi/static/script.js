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

    notify(subObj, type=null) {
        if (this.listeners.length > 0) {
            this.listeners.forEach(listener => listener.update(subObj, type));
        }
    }
}


class SubstanceView{


    constructor(form, model, show_all=false) {
        this.show_all = show_all;
        this.target = form;
        model.addListener(this);
    }

    update(model, type){
        if (type == "substance"){
            this.set_substance(model);
        }
    }

    set_substance(model){
        // do something
    }

    init(model){
        let substance = model.substance;
        let substances = model.valid_substances;
        let shortlist = model.SUB_SHORTLIST;

        let subsel = $(this.target);
        // Loop over the substances, create option group for each category
        Object.keys(substances).forEach(subgrp => {
            let optgroup = $('<optgroup>');
            optgroup.attr('label',subgrp);
            substances[subgrp].forEach(substance => {
                if (this.show_all || shortlist.includes(substance)) {
                    optgroup.append($("<option>").val(subgrp+"."+substance).text(substance));
                }
            });
            subsel.append(optgroup);
        });
        subsel.val(substance);
        // TODO implement onchange
    }
}

// An instance of observable that will hold the current unit configuration and
// notify when it is changed
class UnitView{

    constructor(form, model) {
        this.target = form;
        model.addListener(this);
    }

    update(model, type){
        if (type == "unit"){
            this.set_units(model);
        }
    }

    init(model){
        // Get the unit JSON from the data
        let units = model.units;
        let valid_units = model.valid_units;

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
            $(this.target).append($li.append($label).append($select));
        });
        // TODO - implement onchange
    }

    set_units(model){
        // do something
    }

    cfgAsJSON(){
        return Object.fromEntries(new FormData(document.getElementById("unitform")));
    }
}


class PointModel extends Subject{
    SUB_SHORTLIST=["H2O","C2H4F4","air","O2", "N2"];
    DEFAULT_SUBSTANCE = 'mp.H2O'

    constructor() {
        super();
        this.points = []
        this.point_id = 1;

        this.units = null;
        this.valid_units = null;

        this.substance = null;
        this.valid_substances = null;
    }

    set_units(units, valid_units=null){
        if (valid_units !== null){
            this.valid_units = valid_units;
        }
        this.units = units;
        this.clearpoints();
        this.notify(this,"unit")
    }

    set_substance(substance, valid_substances=null){
        if (valid_substances !== null){
            this.valid_substances = valid_substances;
        }
        this.substance = substance;
        this.clearpoints();
        this.notify(this,"substance")
    }

    add_point(point){
        if (this.points.length === 0){
            this.points = {};
            this.points['ptid'] = [this.point_id];
            for (const key in point) {
                this.points[key] = [point[key]];
            }
        } else {
            this.points['ptid'].push(this.point_id);
            for (const key in point) {
                this.points[key].push(point[key]);
            }
        }
        this.point_id++;
        this.notify(this, "point")
    }

    delete_point(id){
        let index = this.points['ptid'].indexOf(id);
        for (const key in this.points) {
            this.points[key].splice(index, 1);
        }
        this.notify(this, "point");
    }

    clearpoints(){
        this.points = [];
        this.notify(this, "init");
    }
}

class PlotView{
    constructor(target, model) {
        // TODO - variable plot x- and y-axes
        this.x_prop = 's';
        this.y_prop = 'T';
        this.dispprops = ['T','s','p','v'];
        this.target = target;
        this.container = document.getElementById(target);
        model.addListener(this);
        this.init(model);
    }

    init(model){
        this.set_layout();
        let traces = [{
            x: [],
            y: [],
            customdata: [],
            mode: 'markers',
            hovertemplate: "<b> Point prop<br>"+
                this.x_prop+": %{x}<br>" +
                this.y_prop+": %{y}<br>" +
                "attr: %{customdata: .2f}",
            type: 'scatter'
        }];
        Plotly.newPlot(this.container, traces, this.layout);
        this.setupPlotClickListener();
    }

    setupPlotClickListener(){
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
                let unitFormData = pointModel.units;
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

    set_layout(){
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

    update(model, type){
        if (type == "point"){
            this.updatePoints(model);
        } else if (type == "init") {
            this.init(model);
        }
    }

    updatePoints(model) {
        // Build the customdata object for the tooltip
        // Object has the form [[h1,v1,s1],[h2,v2,s2],[h3,v3,s3]]
        let points = model.points;

        let allkeys = Object.keys(points);
        let customdataset = [];  // The custom data that will be added to the tooltip
        let keylist = [];
        for (let i=0; i<points['T'].length; i++ ){  // Loop over all points
            let arr = [] // Build an array of all props for this index.
            arr.push(points['ptid'][i]); // Make the index the very first datapoint.

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

class TableView{
    // delete rows? https://stackoverflow.com/questions/64526856/how-to-add-edit-delete-buttons-in-each-row-of-datatable
    constructor(target, model) {
        this.dispprops = ['T','p','d','h','s'];
        this.target = target;
        model.addListener(this);

        // Build the data table with null content. Insert the delete button in the extra column.
        let table = new DataTable(this.target, {
            "columnDefs": [ {
                "targets": -1,
                "data": null,
                "defaultContent": "<button id='click2del'>Delete</button>"
            } ]
        });

        $(this.target + ' tbody').on( 'click', 'button', function () {
            var data = table.row( $(this).parents('tr') ).data();
            model.delete_point(data[0]);
        } );
        this.table = table;

        this.init();
    }

    init(){
        this.table.clear().draw();
    }

    update(model, type){
        if (type == "point"){
            this.updatePoints(model);
        } else if (type == "init") {
            this.init();
        }
    }



    updatePoints(model) {
        let points = model.points;

        this.table.rows().remove();

        let customdataset = [];  // The custom data that will be added to the tooltip
        for (let i=0; i<points['ptid'].length; i++ ){  // Loop over all points
            let arr = [] // Build an array of all props for this index.
            arr.push(points['ptid'][i]);
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


// *********************************************
// * PAGE SETUP
// *********************************************

// Instantiate the classes
var unitView;
var substanceView;
var plotView;
var tableView;
var pointModel;


// Execute when the page loads
$(document).ready(function(){
    pointModel = new PointModel();

    getInfo((data)=>{
        unitView = new UnitView('#unitform', pointModel);
        substanceView = new SubstanceView('#sel_substance', pointModel);
        tableView = new TableView('#proptable', pointModel);
        plotView = new PlotView("plot", pointModel);

        pointModel.set_units(data.units, data.valid_units);
        pointModel.set_substance(pointModel.DEFAULT_SUBSTANCE, data.substances);



        unitView.init(pointModel);
        substanceView.init(pointModel);
    });
});



// *********************************************
// * DATA DISPLAY
// *********************************************

function onUnitsChanged(infoMaster){
    // TODO - Handle behavior when units change
}
function onSubstanceChanged(infoMaster){
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
//     plotView.updatePoints(point);
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
    pointModel.add_point(data.data);
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
    let unitFormData = pointModel.units;
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


function getInfo(callback){
    // Get all the PM info.
    $.get("/info",
        callback,
        dataType='json')  // Data type of the response.
        .fail(propResponseFail);  // What to do if it doesn't work
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


