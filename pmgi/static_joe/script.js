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
// * CONTROLLER
// *********************************************

// Define the classes
var unitFormView;
var substanceFormView;
var propChooserView;
var isolineChooserView;
var propEntryView;
var plotView;
var tableView;
var pointModel;


// Execute when the page loads
function init_page() {
    // Instantiate classes with their targets
    pointModel = new DataModel();
    unitFormView = new UnitFormView('unit_controls');
    substanceFormView = new SubstanceFormView('substance_controls');
    propChooserView = new PropChooserView("property_selection", PropChooserView.EVENT_PROPERTY_VISIBILITY);
    isolineChooserView = new PropChooserView("isoline_selection", PropChooserView.EVENT_ISOLINE_VISIBILITY, ['T', 'd', 'p', 's', 'h', 'x']);
    propEntryView = new PropEntryView("property_controls");
    tableView = new TableView('property_table');
    plotView = new PlotView("plot_display");

    // getInfo is an async request, so use the callback to complete setup.
    getInfo((data) => {
        // Get the general info data, assign to model
        pointModel.init_info(data.data.legalunits, data.data.substances);
        set_units(data.units);
        set_substance(pointModel.DEFAULT_SUBSTANCE);

        // Assign views to listen to the main model
        pointModel.addListener(unitFormView);
        pointModel.addListener(substanceFormView);
        pointModel.addListener(tableView);
        pointModel.addListener(plotView);
        pointModel.addListener(propChooserView);
        pointModel.addListener(isolineChooserView);
        pointModel.addListener(propEntryView);

        // Assign views to listen to the views that hold state data
        propChooserView.addListener(tableView);
        propChooserView.addListener(plotView);

        isolineChooserView.addListener(plotView);

        // Call inits on views now that the properties exist
        tableView.init(get_output_properties());
        plotView.init();
        unitFormView.init(get_valid_units(), get_units());
        substanceFormView.init(get_valid_substances(), get_substance(), get_display_substances());
        propChooserView.init(get_output_properties(), pointModel.DEFAULT_PROP_OUT_SHORTLIST);
        isolineChooserView.init(get_output_properties(), ['T', 'p', 'x']);
        propEntryView.init(get_input_properties(), get_unit_strings());
    });
}


// Passthrough controller functions that get/set on behalf of the model

function get_output_properties(){
    // TODO - consider where this belongs
    return pointModel.get_output_properties();
}

function get_input_properties(){
    return pointModel.get_input_properties();
}

function get_display_substances(){
    return pointModel.DEFAULT_SUB_SHORTLIST;
}

function get_valid_units(){
    return pointModel.get_valid_units();
}

function get_valid_substances(){
    return pointModel.get_valid_substances();
}

function get_points(){
    return pointModel.get_points();
}

function add_point(point){
    pointModel.add_point(point);
}

function delete_point(point){
    pointModel.delete_point(point)
}

function get_auxlines(){
    return pointModel.get_auxlines();
}

function set_substance(newsubstance){
    pointModel.set_substance(newsubstance);
    calc_auxline();
}

function calc_auxline(){
    if (get_substance().startsWith('mp')){
        compute_auxline((data)=>{
            let sll = data.data['liquid'];
            let svl = data.data['vapor'];
            // concatenate vapor to liquid
            Object.keys(svl).forEach(key => {
                for (let i = svl[key].length; i > -1; i--) {
                    sll[key].push(svl[key][i]);
                }
            });
            add_steamdome(sll);
        });

        compute_auxline((data)=>{
            data.data.data.forEach((line)=>{
                pointModel.add_auxline('x', line, 'global');
            });
        },{'x': 0, 'default': true});
    }

    // Add a few types of lines
    ['p', 'T', 'd', 'h', 's'].forEach((prop_val)=>{
        compute_args = {};
        compute_args[prop_val] = 0;
        compute_args["default"] = true;
        compute_auxline((data)=>{
            data.data.data.forEach((line)=>{
                pointModel.add_auxline(prop_val, line, 'global');
            });
        },compute_args);
    })
}

function add_steamdome(steamdome){
    pointModel.add_auxline('steamdome', steamdome, parent='global');
}

function get_substance(){
    return pointModel.get_substance();
}

function get_units(){
    return pointModel.get_units();
}

function get_unit_strings(props=[]){
    return pointModel.get_units_for_prop(props);
}

function set_units(units){
    pointModel.set_units(units);
    if (get_substance() != null){
        calc_auxline();
    }
}

// *********************************************
// * CONTROLLER - AJAX
// *********************************************


/**
 * Async request for getting a state from the backend.
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_point(props, mode="POST"){
    let requestroute = "/state";

    // Add the substance ID to props always
    props['id'] = get_substance();

    // TODO - Callbacks are hardcoded, keep or lose?
    if (mode === "GET"){
        $.get(
            requestroute,
            props,
            propResponseSuccess,
            dataType='json');
    } else if (mode === "POST") {
        // Build the data request
        let postData = Object.assign({}, props); // clone it
        postData.units = get_units();  // add the units on
        $.ajax({
            url: requestroute,
            type: "POST",
            data: JSON.stringify(postData),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: propResponseSuccess,
        });
    }
}

/**
 * Async request for getting a state from the backend.
 * @param callback - function handle to execute when complete
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_auxline(callback, props={}, mode="POST"){
    let requestroute;
    if (Object.keys(props).length === 0) {
        requestroute = "/saturation";
    } else {
        requestroute = "/isoline"
    }

    // Add the substance ID to props always
    props['id'] = get_substance();

    if (mode === "GET"){
        $.get(requestroute, props, callback,dataType='json');
    } else if (mode === "POST") {
        let postData = Object.assign({}, props); // clone it
        postData.units = get_units();  // add the units on
        $.ajax({
            url: requestroute,
            type: "POST",
            data: JSON.stringify(postData),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: callback
        });
    }
}

/**
 * Async request to get global info
 * @param callback - a function handle for the response success
 */
function getInfo(callback){
    // Get all the PM info.
    $.get("/info",
        callback,
        dataType='json');  // Data type of the response.

}

/**
 * Callback for when a point data request completes
 * @param data - JSON data from the flask backend
 */
function propResponseSuccess(data){
    add_point(data.data);
}





