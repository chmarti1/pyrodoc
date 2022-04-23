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
    static EVENT_ID_NULL = null;

    constructor() {
        this.listeners = [];
    }

    /**
     * Add a listener to the object
     * @param listener - Object: must contain listener.update(source, event, data)
     */
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

    /**
     * Notify all listeners of events
     * @param source - Object: the origin object that created the event
     * @param event - String: an indicator of the event type (or null)
     * @param data - Various: data associated with the event (or null)
     */
    notify(source, event=Subject.EVENT_ID_NULL, data=null) {
        if (this.listeners.length > 0) {
            this.listeners.forEach(listener => listener.update(source, event, data));
        }
    }
}


class PointModel extends Subject{
    static EVENT_UNIT = 'unit';
    static EVENT_SUBSTANCE = 'substance';
    static EVENT_POINT = 'point'
    static EVENT_INIT = 'init';

    SUB_SHORTLIST=["mp.H2O","mp.C2H2F4","ig.air","ig.O2", "ig.N2"];
    PROP_SHORTLIST=["T","p","v","e","h","s","x"];
    DEFAULT_SUBSTANCE = 'mp.H2O'
    INIT_ID = 1

    constructor() {
        super();
        this.points = []
        this.point_id = this.INIT_ID;

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
        this.notify(this, PointModel.EVENT_UNIT, this.get_units())
    }

    get_valid_properties(){
        return this.valid_substances[this.substance]['props'];
    }

    get_units(){
        return this.units;
    }

    get_substance(){
        return this.substance;
    }

    get_valid_units(){
        return this.valid_units;
    }

    get_valid_substances(){
        return this.valid_substances;
    }

    set_substance(substance, valid_substances=null){
        if (valid_substances !== null){
            this.valid_substances = valid_substances;
        }
        this.substance = substance;
        this.clearpoints();
        this.notify(this, PointModel.EVENT_SUBSTANCE, this.get_substance())
    }

    get_points(){
        return this.points;
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
        this.notify(this, PointModel.EVENT_POINT, this.get_points())
    }

    delete_point(id){
        let index = this.points['ptid'].indexOf(parseInt(id));
        for (const key in this.points) {
            this.points[key].splice(index, 1);
        }
        if (this.points['ptid'].length == 0){
            this.clearpoints();
        } else {
            this.notify(this, PointModel.EVENT_POINT, this.get_points());
        }
    }

    clearpoints(){
        this.points = [];
        this.point_id = this.INIT_ID;
        this.notify(this, PointModel.EVENT_INIT, null);
    }
}



class SubstanceFormView{

    constructor(formHTMLid, show_all=false) {
        this.show_all = show_all;
        this.target = formHTMLid;
    }

    update(source, event, data){
        if (event == PointModel.EVENT_SUBSTANCE){
            this.set_value(data);
        }
    }

    set_value(substance){
        $(this.target).val(substance);
    }

    init(substances, current_value, shortlist=null){

        let subsel = $(this.target);
        // Loop over the substances, create option group for each category
        Object.keys(substances).forEach(subst => {
            if (this.show_all || shortlist == null || shortlist.includes(subst)) {
                    subsel.append($("<option>").val(subst).text(subst));
            }
        });

        // The event handler for changes, which provides a confirmation.
        subsel.on("change", ()=>{
            let success = confirm('Changing the substance will reset all data. Are you sure?');
            if(success){
                set_substance(subsel.val());
            } else {
                // undo
                this.set_value(get_substance());
                return false;
            }
        });

        this.set_value(current_value);
    }
}


class UnitFormView{

    constructor(formHTMLid) {
        this.target = formHTMLid;
        this.button_apply = "#unit_apply";
        this.button_revert = "#unit_revert";
        this.button_hide = "#unit_hide"
        this.unit_list_div = "#hideablelist";

        this.apply_onclick = this.apply_onclick.bind(this);
        this.revert_onclick = this.revert_onclick.bind(this);
        $(this.button_apply).on("click", this.apply_onclick);
        $(this.button_revert).on("click", this.revert_onclick);

        this.hide_onclick = this.hide_onclick.bind(this);
        $(this.button_hide).on("click", this.hide_onclick);
    }


    update(source, event, data){
        if (event == PointModel.EVENT_UNIT){
            this.set_values(data);
        }
    }

    /**
     * Create the selects for the unit form
     * @param valid_units Expects an Object with keys of the unit categories and values of arrays of the allowable unit values for that unit category
     * @param current_values Expects an Object with keys of the unit categories and values of the current unit for that unit category
     */
    init(valid_units, current_values){

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

            $select.on("change", ()=>{
                $(this.button_apply).show();
                $(this.button_revert).show();
            });
            // Add the objects to the form
            $(this.target).append($li.append($label).append($select));
        });
        // Set all the values
        this.set_values(current_values);
    }

    set_values(units){
        // Copy the values from a dict
        Object.keys(units).forEach(key => {
            let selobj = $('[name="'+key+'"]');
            selobj.val(units[key]);
        });
    }



    apply_onclick(){
        let success = confirm('Changing the units will reset all data. Are you sure?');
            if(success){
                // Pass the units to the controller
                set_units(this.valuesAsJSON())
                $(this.button_apply).hide();
                $(this.button_revert).hide();
            } else {
                // do nothing and let the user figure it out
                return false;
            }

    }

    revert_onclick(){
        // revert back to what was set previously
        this.set_values(get_units());
        $(this.button_apply).hide();
        $(this.button_revert).hide();
    }

    hide_onclick(){
        $(this.unit_list_div).toggle();
    }

    valuesAsJSON(){
        // Convert the values to a dict
        return Object.fromEntries(new FormData($(this.target)[0]));
    }
}


class PropFormView extends Subject{
    static EVENT_PROPERTY_VISIBILITY = 'propvis';
    constructor(formHTMLid) {
        super();
        this.target = formHTMLid;
        this.hide_checks = "#propchoice_hide";
        this.prop_checks = "#propchecks";
        this.prop_table = "#propinput";
        this.prop_form = "#propform";

        this.get_button = "#get_props";
        this.post_button = "#post_props";

        this.checkbox_onchange = this.checkbox_onchange.bind(this);

        this.hide_onclick = this.hide_onclick.bind(this);
        $(this.hide_checks).on("click", this.hide_onclick);


        this.get_onclick = this.get_onclick.bind(this);
        this.post_onclick = this.post_onclick.bind(this);
        $(this.get_button).on("click", this.get_onclick);
        $(this.post_button).on("click", this.post_onclick);
    }

    update(source, event, data) {
        if (event == PointModel.EVENT_SUBSTANCE) {
            let disp_props = this.get_checkbox_values();
            let prop_vals = this.valuesToJSON();
            this.init(get_valid_properties(), disp_props, prop_vals);
        } else if (event == PointModel.EVENT_INIT) {
            //I think we're good?
        }
    }

    init(valid_properties, show_properties, prop_values=null) {
        this.create_checkboxes(valid_properties);
        this.set_checkbox_values(show_properties);

        this.create_propform(this.get_checkbox_values());
        this.set_form_values(prop_values);

        this.notify(this,PropFormView.EVENT_PROPERTY_VISIBILITY, this.get_checkbox_values());
    }

    create_checkboxes(valid_properties) {
        $(this.prop_checks).empty();
        // Loop over all the configured unit types
        valid_properties.forEach(prop => {
            // The form will be a list of labelled check boxes
            let $li = $("<li>")
            let $label = $('<label>' + prop + '</label>', {});

            let $checkbox = $('<input>',{type: "checkbox", value: prop, id: prop+'_box', name: prop+'_box'});
            $checkbox.on("click", this.checkbox_onchange);
            // Add the objects to the form
            $(this.prop_checks).append($li.append($label).append($checkbox));
        });
    }

    checkbox_onchange(){
        let disp_props = this.get_checkbox_values();
        let prop_vals = this.valuesToJSON();
        this.create_propform(disp_props);
        this.set_form_values(prop_vals);
        this.notify(this,PropFormView.EVENT_PROPERTY_VISIBILITY,disp_props);
    }

    create_propform(props) {
        $(this.prop_table).empty();

        let head = "<thead><tr>"
        props.forEach((prop) => {
            head = head + "<th>" + prop + "</th>";
        });
        head = head + "</tr></thead>";

        $(this.prop_table).append(head);

        let tr = $("<tr>")
        props.forEach((prop) => {
            let td = $("<td>");
            let inputbox = '<input type="text" propvalue="' + prop + '" id="' + prop + '_input" name="' + prop + '_input">';
            tr.append(td.append(inputbox));
        });
        $(this.prop_table).append(tr);
    }

    get_checkbox_values() {
        let names = [];
        $(this.prop_checks + ' input:checked').each((id, box) => {
            names.push(box.value);
        });
        return names;
    }

    set_checkbox_values(show_properties) {

        $(this.prop_checks + ' input').each((id, box) => {
            let prop = box.value;
            let checked = show_properties.includes(prop);
            if (checked) {
                box.checked = true;
            } else {
                box.checked = false;
            }
        });
    }

    set_form_values(props) {
        if (props != null) {

            $(this.prop_form + ' input').each((id, box) => {
                let boxkey = box.attributes['propvalue'].nodeValue;
                if (Object.keys(props).includes(boxkey)) {
                    box.value = props[boxkey];
                }
            });
        }
    }

    valuesToJSON() {
        let outdata = {};
        $(this.prop_form+ " input").each((id, box) =>{
            let value = box.value;
            if (value !== ""){
                let prop = box.attributes['propvalue'].nodeValue;
                outdata[prop] = value;
            }
        });
        return outdata;
    }

    get_onclick(){
        compute_point(this.valuesToJSON(), "GET");
    }

    post_onclick(){
        compute_point(this.valuesToJSON(), "POST");
    }

    hide_onclick(){
        $(this.prop_checks).toggle();
    }

}


class PlotView{
    constructor(divTarget) {
        // TODO - variable plot x- and y-axes
        this.x_prop = 's';
        this.y_prop = 'T';
        this.dispprops = ['T','s','p','v'];
        this.target = divTarget;
        this.container = document.getElementById(divTarget);
        this.init();
    }

    init(){
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
                formData[myPlotContainer.x_prop] = x
                formData[myPlotContainer.y_prop] = y
                compute_point(formData, "POST");
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

    update(source, event, data){
        if (event == PointModel.EVENT_POINT){
            this.updatePoints(data);
        } else if (event == PointModel.EVENT_INIT) {
            this.init();
        }
    }

    updatePoints(points) {
        // Build the customdata object for the tooltip
        // Object has the form [[h1,v1,s1],[h2,v2,s2],[h3,v3,s3]]

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
    // showhide columns https://datatables.net/examples/api/show_hide.html
    constructor(divTarget) {
         // TODO - switch to dynamic show/hide
        this.target = divTarget;
        this.table = null
    }

    init(props){
        this.dispprops = [...props];
        this.dispprops.unshift("ptid");
        if (this.table == null){
            let $tablediv = $(this.target);
            let $head = $('<thead></thead>');
            let $foot = $('<tfoot></tfoot>');
            let $r = $('<tr></tr>')
            this.dispprops.forEach((prop) =>{
                let $th = $('<th>'+prop+'</th>');
                $r.append($th);
            });
            $r.append('<th>Ctrl</th>');
            $head.append($r);
            //$foot.append($r);
            $tablediv.append($head);
            //$tablediv.append($foot);


            // Build the data table with null content. Insert the delete button in the extra column.
            let table = new DataTable(this.target, {
                "columnDefs": [ {
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button id='click2del'>Delete</button>"
                } ]
            });

            $(this.target + ' tbody').on( 'click', 'button', function () {
                let data = table.row( $(this).parents('tr') ).data();
                delete_point(data[0]);
            } );
            this.table = table;
        }

        this.table.clear().draw();
    }

    update(source, event, data){
        if (event == PointModel.EVENT_POINT){
            this.updatePoints(data);
        } else if (event == PointModel.EVENT_INIT) {
            this.init();
        } else if (event == PropFormView.EVENT_PROPERTY_VISIBILITY) {
            this.columnVisibility(data);
        }
    }

   columnVisibility(columns){

        this.table.columns().every((ind) => {
            let col = this.table.column(ind);
            let name = col.header().textContent
            if (columns.includes(name) || name=="ptid" || name=="Ctrl"){
                col.visible(true);
            } else {
                col.visible(false);
            }
        });

   }

    updatePoints(points) {

        this.table.rows().remove();

        let customdataset = [];
        for (let i=0; i<points['ptid'].length; i++ ){  // Loop over all points
            let arr = [] // Build an array of all props for this index.
            //arr.push(points['ptid'][i]);
            this.dispprops.forEach(key => {
                arr.push(points[key][i].toLocaleString('en-US',{
                    maximumSignificantDigits: 5
                }));
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
var unitFormView;
var substanceFormView;
var propFormView;
var plotView;
var tableView;
var pointModel;


// Execute when the page loads
$(document).ready(function(){
    pointModel = new PointModel();
    unitFormView = new UnitFormView('#unitform');
    substanceFormView = new SubstanceFormView('#sel_substance');
    propFormView = new PropFormView("#property_controls")
    tableView = new TableView('#proptable');
    plotView = new PlotView("plot");

    getInfo((data)=>{
        pointModel.set_units(data.units, data.valid_units);
        pointModel.set_substance(pointModel.DEFAULT_SUBSTANCE, data.substances);

        pointModel.addListener(unitFormView);
        pointModel.addListener(substanceFormView);
        pointModel.addListener(tableView);
        pointModel.addListener(plotView);
        pointModel.addListener(propFormView);

        propFormView.addListener(tableView);

        tableView.init(get_valid_properties());
        unitFormView.init(get_valid_units(), get_units());
        substanceFormView.init(get_valid_substances(), get_substance(), get_display_substances());
        propFormView.init(get_valid_properties(), pointModel.PROP_SHORTLIST);
    });
});


function get_valid_properties(){
    // TODO - consider where this belongs
    return pointModel.get_valid_properties();
}

function get_display_substances(){
    // TODO - consider where this belongs
    return pointModel.SUB_SHORTLIST;
}

function get_points(){
    return pointModel.get_points();
}

function delete_point(point){
    pointModel.delete_point(point)
}

function get_valid_substances(){
    return pointModel.get_valid_substances();
}

function get_substance(){
    return pointModel.get_substance();
}

function get_units(){
    return pointModel.get_units();
}

function get_valid_units(){
    return pointModel.get_valid_units();
}

function set_substance(newsubstance){
    pointModel.set_substance(newsubstance);
}

function set_units(units){
    pointModel.set_units(units);
}

function add_point(point){
    pointModel.add_point(point);
}

// TODO - Expand/contract table display based on property selection

function compute_point(props, mode="POST"){
    let requestroute = "/";

    // Add the substance ID to props
    props['id'] = get_substance();

    if (mode == "GET"){
        $.get(requestroute, props, propResponseSuccess,dataType='json')
            .fail(propResponseFail);
    } else if (mode == "POST") {
        let postData = {state_input: props, units: get_units()};
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
}

function getInfo(callback){
    // Get all the PM info.
    $.get("/info",
        callback,
        dataType='json')  // Data type of the response.
        .fail(propResponseFail);  // What to do if it doesn't work
}


// *********************************************
// * INTERACTIVITY
// *********************************************



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
    add_point(data.data);
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





